"""
    File: visualizer.py
  Author: Ian Featherston
    Date: 04/29/2025
    Desc: This script holds the DataframeVisualizer class uses matplotlib to 
            help present data in a more readable way.
"""
import os

import pandas as pd
import matplotlib.pyplot as plt

from utilities.logger import setup_logger

class DataframeVisualizer:
    """
    This class converts DataFrames into visual data vai Matplotlib and NumPy.
    """
    def __init__(self):
        """
        Initializes the DataframeVisualizer class
        """
        self.logger = setup_logger()

        self.file_ext = '.png'
        self.folder = 'figures'         # Where the figures are stored

        # If our target directory doesn't exist, create it
        os.makedirs(self.folder, exist_ok=True)


    def store_report(self, fig: plt.Figure, filename: str):
        """
        Stores the passed figure as a file.

        Parameters:
            fig (plt.Figure): The figure to store
            filename (str): Output filename
        """
        # Check for file extension
        if not filename.endswith(self.file_ext):
            filename += self.file_ext

        # Save the figure to the folder specified by self.folder
        filename = os.path.join(self.folder, filename)

        try:
            fig.tight_layout()
            fig.savefig(filename, dpi=300)
            self.logger.info("Report saved to '%s'.", filename)
        except IOError as e:
            self.logger.error("Error storing '%s': %s", filename, e)


    def display_all_figures(self):
        """
        Displays all figures in the current session.
        """
        plt.show()


    def close_all_figures(self):
        """
        Closes all figures in the current session.
        """
        plt.close('all')


    def plot_revenue_over_time(self, df: pd.DataFrame) -> plt.Figure:
        """
        Plots the revenue made over time (months)

        Parameters:
            df (pd.DataFrame): The report_revenue DataFrame
        Returns:
            plt.Figure: The Matplotlib figure as an object
        """
        self.logger.info('Plotting revenue over time')
        try:
            df = df.copy()

            # Convert revenue string back to float for plotting
            df['revenue_float'] = (
                df['total_revenue']
                .replace(r'[\$,]', '', regex=True)
                .astype(float)
            )

            # Assign our figure object to 'fig'
            fig, ax = plt.subplots(figsize=(12,6))

            # Plot revenue
            ax.plot(
                df['month'],
                df['revenue_float'],
                label='Revenue ($)',
                color='green',
                marker='o'
            )

            # Graph properties
            ax.set_title('Monthly Revenue')
            ax.set_xlabel('Month')
            ax.set_ylabel('Revenue')
            ax.legend()
            ax.grid(True)
            fig.tight_layout()
            plt.xticks(rotation=45)

            return fig

        except (KeyError, ValueError, TypeError) as e:
            self.logger.error("Error while plotting revenue over time: %s", e)


    def plot_company_stats(self, df: pd.DataFrame, company_name: str) -> plt.Figure:
        """
        Plots a specific company's statistics over time.

        Parameters:
            df (pd.DataFrame): The report_company DataFrame
            company_name (str): The name of the company to plot
        Returns:
            plt.Figure: The Matplotlib figure as an object
        """
        self.logger.info('Plotting company statistics')

        # Convert avg_dollar_per_event & bid_total from string back to float
        df['avg_dollar_per_event'] = (
            df['avg_dollar_per_event']
            .replace(r'[\$,]', '', regex=True)
            .astype(float)
        )
        df['bid_total'] = (
            df['bid_total']
            .replace(r'[\$,]', '', regex=True)
            .astype(float)
        )

        try:
            df = df.copy()

            # Assign our figure object to 'fig'
            fig, ax = plt.subplots(figsize=(12,6))

            # Plot avg_dollar_per_event
            ax.plot(
                df['month'],
                df['avg_dollar_per_event'],
                label='Avg $ per Event',
                color='green',
                marker='o'
            )

            # Plot bid_total
            ax.plot(
                df['month'],
                df['bid_total'],
                label='Total Bid ($)',
                color='blue',
                marker='o'
            )

            # Plot num_auctions
            ax.plot(
                df['month'],
                df['num_auctions'],
                label='Total Auctions',
                color='red',
                marker='o'
            )

            # Graph properties
            ax.set_title(f"Company Statistics for {company_name}")
            ax.set_xlabel('Month')
            ax.set_ylabel('Value')
            ax.legend()
            ax.grid(True)
            fig.tight_layout()
            plt.xticks(rotation=45)

            return fig

        except (KeyError, ValueError, TypeError) as e:
            self.logger.error("Error while plotting company statistics: %s", e)


    # This was experimental, and ended up not using it
    def plot_line_chart(self,
                        df: pd.DataFrame,
                        x_col: str,
                        fig_title: str = '',
                        x_label: str = '',
                        y_label: str = '',
                        markers: str = 'o',
                        colormap: str = 'tab10'
    ) -> plt.Figure:
        """
        Dynamically plots multiple columns against a single x-axis column.

        Parameters:
            df (pd.DataFrame): Data to plot
            x_col (str): Column for the x-axis
            fig_title (str): Title of the plot
            x_label (str): Label for x-axis (defaults to x_col)
            y_label (str): Label for y-axis
            markers (str): Marker style
            colormap (str): Matplotlib colormap name (e.g. 'tab10', 'Set1', etc.)

        Returns:
            plt.Figure: The generated Matplotlib figure
        """
        self.logger.info("Potting multi-line chart '%s'", fig_title)

        try:
            df = df.copy()
            fig, ax = plt.subplots(figsize=(12, 6))

            colors = plt.get_cmap(colormap)
            numeric_cols = df.select_dtypes(include=['number']).columns.drop(x_col, errors='ignore')

            # Plot each numeric column against the x_col
            for i, col in enumerate(numeric_cols):
                ax.plot(
                    df[x_col],
                    df[col],
                    label=col,
                    color=colors(i % colors.N),
                    marker=markers
                )

            # Figure properties
            ax.set_title(fig_title)
            ax.set_xlabel(x_label if x_label else x_col)
            ax.set_ylabel(y_label or 'Value')
            ax.legend()
            ax.grid(True)
            fig.tight_layout()
            plt.xticks(rotation=45)

            return fig

        except (KeyError, ValueError, TypeError) as e:
            self.logger.error("Error while plotting multi-line chart: %s", e)
            return None

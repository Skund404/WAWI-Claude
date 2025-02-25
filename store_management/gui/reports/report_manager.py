# report_manager.py
"""
Report Manager module for generating and managing reports.

This module provides functionality to generate various types of reports,
such as inventory reports, sales reports, and production reports.
It utilizes the SQLAlchemy ORM to retrieve data from the database and
generates reports in different formats like CSV, PDF, and HTML.
"""

import csv
import logging
from typing import List, Dict, Any

from sqlalchemy.exc import SQLAlchemyError
from models import Inventory, Sales, Production
from utils.database import DatabaseManager
from utils.pdf_generator import PDFGenerator
from utils.html_generator import HTMLGenerator

# Configure logging
logger = logging.getLogger(__name__)


class ReportManager:
    """
    Class for managing and generating reports.

    Methods:
        generate_inventory_report: Generate an inventory report.
        generate_sales_report: Generate a sales report.
        generate_production_report: Generate a production report.
    """

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize the ReportManager.

        Args:
            db_manager (DatabaseManager): Database manager instance.
        """
        self.db_manager = db_manager

    def generate_inventory_report(self, format: str = 'csv') -> str:
        """
        Generate an inventory report.

        Args:
            format (str): Report format ('csv', 'pdf', or 'html'). Default is 'csv'.

        Returns:
            str: Generated report filename.
        """
        try:
            # Retrieve inventory data from the database
            with self.db_manager.session_scope() as session:
                inventory_data = session.query(Inventory).all()

            # Prepare report data
            report_data = [
                ['Product ID', 'Product Name', 'Quantity', 'Location']
            ]
            for item in inventory_data:
                report_data.append([
                    item.product_id,
                    item.product_name,
                    item.quantity,
                    item.location
                ])

            # Generate report based on the specified format
            if format == 'csv':
                return self._generate_csv_report('inventory_report.csv', report_data)
            elif format == 'pdf':
                return self._generate_pdf_report('inventory_report.pdf', report_data)
            elif format == 'html':
                return self._generate_html_report('inventory_report.html', report_data)
            else:
                raise ValueError(f"Unsupported report format: {format}")

        except SQLAlchemyError as e:
            logger.exception("Error occurred while generating inventory report.")
            raise

    def generate_sales_report(self, start_date: str, end_date: str, format: str = 'csv') -> str:
        """
        Generate a sales report for a given date range.

        Args:
            start_date (str): Start date of the sales report.
            end_date (str): End date of the sales report.
            format (str): Report format ('csv', 'pdf', or 'html'). Default is 'csv'.

        Returns:
            str: Generated report filename.
        """
        try:
            # Retrieve sales data from the database
            with self.db_manager.session_scope() as session:
                sales_data = session.query(Sales)\
                    .filter(Sales.date >= start_date)\
                    .filter(Sales.date <= end_date)\
                    .all()

            # Prepare report data
            report_data = [
                ['Date', 'Product', 'Quantity', 'Revenue']
            ]
            for sale in sales_data:
                report_data.append([
                    sale.date,
                    sale.product,
                    sale.quantity,
                    sale.revenue
                ])

            # Generate report based on the specified format
            if format == 'csv':
                return self._generate_csv_report('sales_report.csv', report_data)
            elif format == 'pdf':
                return self._generate_pdf_report('sales_report.pdf', report_data)
            elif format == 'html':
                return self._generate_html_report('sales_report.html', report_data)
            else:
                raise ValueError(f"Unsupported report format: {format}")

        except SQLAlchemyError as e:
            logger.exception("Error occurred while generating sales report.")
            raise

    def generate_production_report(self, month: str, format: str = 'csv') -> str:
        """
        Generate a production report for a given month.

        Args:
            month (str): Month for the production report.
            format (str): Report format ('csv', 'pdf', or 'html'). Default is 'csv'.

        Returns:
            str: Generated report filename.
        """
        try:
            # Retrieve production data from the database
            with self.db_manager.session_scope() as session:
                production_data = session.query(Production)\
                    .filter(Production.month == month)\
                    .all()

            # Prepare report data
            report_data = [
                ['Month', 'Product', 'Quantity']
            ]
            for item in production_data:
                report_data.append([
                    item.month,
                    item.product,
                    item.quantity
                ])

            # Generate report based on the specified format
            if format == 'csv':
                return self._generate_csv_report('production_report.csv', report_data)
            elif format == 'pdf':
                return self._generate_pdf_report('production_report.pdf', report_data)
            elif format == 'html':
                return self._generate_html_report('production_report.html', report_data)
            else:
                raise ValueError(f"Unsupported report format: {format}")

        except SQLAlchemyError as e:
            logger.exception("Error occurred while generating production report.")
            raise

    def _generate_csv_report(self, filename: str, data: List[List[Any]]) -> str:
        """
        Generate a CSV report.

        Args:
            filename (str): Name of the CSV file.
            data (List[List[Any]]): Report data.

        Returns:
            str: Generated CSV filename.
        """
        try:
            with open(filename, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerows(data)
            return filename
        except IOError as e:
            logger.exception(f"Error occurred while generating CSV report: {filename}")
            raise

    def _generate_pdf_report(self, filename: str, data: List[List[Any]]) -> str:
        """
        Generate a PDF report.

        Args:
            filename (str): Name of the PDF file.
            data (List[List[Any]]): Report data.

        Returns:
            str: Generated PDF filename.
        """
        try:
            pdf_generator = PDFGenerator()
            pdf_generator.generate(filename, data)
            return filename
        except Exception as e:
            logger.exception(f"Error occurred while generating PDF report: {filename}")
            raise

    def _generate_html_report(self, filename: str, data: List[List[Any]]) -> str:
        """
        Generate an HTML report.

        Args:
            filename (str): Name of the HTML file.
            data (List[List[Any]]): Report data.

        Returns:
            str: Generated HTML filename.
        """
        try:
            html_generator = HTMLGenerator()
            html_generator.generate(filename, data)
            return filename
        except Exception as e:
            logger.exception(f"Error occurred while generating HTML report: {filename}")
            raise
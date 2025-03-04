# scripts/analyze_db_schema.py
"""
Database schema analysis script to identify discrepancies between
SQLAlchemy models and actual database schema.

Run this script to generate a detailed report of all tables, columns,
foreign keys and relationships in both the models and database.
"""

import logging
import sys
from collections import defaultdict
from sqlalchemy import create_engine, inspect, MetaData, Table, text
from sqlalchemy.orm import class_mapper
from sqlalchemy.ext.declarative import DeclarativeMeta

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler(),
                              logging.FileHandler('schema_analysis.log')])
logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import modules
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import database models and connection
from database.models.base import Base
from database.sqlalchemy.session import get_db_session


class SchemaAnalyzer:
    """Analyze database schema and SQLAlchemy models for discrepancies."""

    def __init__(self):
        """Initialize the analyzer with a database session."""
        self.session = get_db_session()
        self.engine = self.session.get_bind()
        self.inspector = inspect(self.engine)
        self.metadata = MetaData()
        self.metadata.reflect(bind=self.engine)
        self.results = {
            'tables': defaultdict(dict),
            'missing_tables': [],
            'extra_tables': [],
            'relationship_issues': [],
            'foreign_key_issues': [],
            'suggestions': []
        }

    def analyze(self):
        """Run full schema analysis."""
        logger.info("Starting schema analysis...")

        # Analyze tables
        self._analyze_tables()

        # Analyze each model
        for model_class in self._get_all_models():
            self._analyze_model(model_class)

        # Generate final report
        self._generate_report()

        logger.info("Schema analysis complete.")
        return self.results

    def _get_all_models(self):
        """Get all SQLAlchemy model classes."""
        models = []

        def get_subclasses(cls):
            all_subclasses = []
            for subclass in cls.__subclasses__():
                all_subclasses.append(subclass)
                all_subclasses.extend(get_subclasses(subclass))
            return all_subclasses

        models = get_subclasses(Base)
        logger.info(f"Found {len(models)} model classes")
        return models

    def _analyze_tables(self):
        """Compare tables in models and database."""
        # Get tables from database
        db_tables = set(self.inspector.get_table_names())

        # Get tables from models
        model_tables = set()
        for model in self._get_all_models():
            if hasattr(model, '__tablename__'):
                model_tables.add(model.__tablename__)

        # Find discrepancies
        missing_tables = model_tables - db_tables
        extra_tables = db_tables - model_tables

        if missing_tables:
            logger.warning(f"Tables defined in models but missing from database: {missing_tables}")
            self.results['missing_tables'] = list(missing_tables)

        if extra_tables:
            logger.info(f"Tables in database but not defined in models: {extra_tables}")
            self.results['extra_tables'] = list(extra_tables)

        # Store all tables
        for table_name in db_tables:
            self.results['tables'][table_name] = {
                'in_database': True,
                'in_models': table_name in model_tables,
                'columns': {},
                'foreign_keys': []
            }

        for table_name in missing_tables:
            self.results['tables'][table_name] = {
                'in_database': False,
                'in_models': True,
                'columns': {},
                'foreign_keys': []
            }

    def _analyze_model(self, model_class):
        """Analyze a specific model and its relationships."""
        if not hasattr(model_class, '__tablename__'):
            logger.warning(f"Model {model_class.__name__} has no __tablename__ attribute")
            return

        table_name = model_class.__tablename__

        try:
            # Get model columns
            mapper = class_mapper(model_class)
            model_columns = {c.key: c for c in mapper.columns}

            # Check if table exists in database
            if table_name not in self.metadata.tables:
                logger.warning(f"Table '{table_name}' defined in model {model_class.__name__} but not in database")

                # Add model columns to results
                for col_name, col in model_columns.items():
                    self.results['tables'][table_name]['columns'][col_name] = {
                        'in_model': True,
                        'in_database': False,
                        'type': str(col.type),
                        'nullable': col.nullable
                    }
                return

            # Get database columns
            db_table = self.metadata.tables[table_name]
            db_columns = {c.name: c for c in db_table.columns}

            # Compare columns
            model_column_names = set(model_columns.keys())
            db_column_names = set(db_columns.keys())

            # Find discrepancies
            missing_columns = model_column_names - db_column_names
            extra_columns = db_column_names - model_column_names

            if missing_columns:
                logger.warning(
                    f"Columns defined in model {model_class.__name__} but missing from table {table_name}: {missing_columns}")
                self.results['suggestions'].append(
                    f"Add missing columns {missing_columns} to table {table_name}"
                )

            if extra_columns:
                logger.info(
                    f"Columns in table {table_name} but not defined in model {model_class.__name__}: {extra_columns}")

            # Store column info
            for col_name in model_column_names.union(db_column_names):
                column_info = {
                    'in_model': col_name in model_column_names,
                    'in_database': col_name in db_column_names
                }

                if col_name in model_columns:
                    model_col = model_columns[col_name]
                    column_info['model_type'] = str(model_col.type)
                    column_info['model_nullable'] = model_col.nullable

                if col_name in db_columns:
                    db_col = db_columns[col_name]
                    column_info['db_type'] = str(db_col.type)
                    column_info['db_nullable'] = db_col.nullable

                self.results['tables'][table_name]['columns'][col_name] = column_info

            # Analyze relationships
            self._analyze_relationships(model_class, table_name)

        except Exception as e:
            logger.error(f"Error analyzing model {model_class.__name__}: {str(e)}")

    def _analyze_relationships(self, model_class, table_name):
        """Analyze relationships defined in the model."""
        try:
            mapper = class_mapper(model_class)

            # Get database foreign keys
            db_fks = []
            if table_name in self.metadata.tables:
                db_fks = self.inspector.get_foreign_keys(table_name)

            # Store foreign keys
            self.results['tables'][table_name]['foreign_keys'] = db_fks

            # Check each relationship
            for rel in mapper.relationships:
                rel_info = {
                    'name': rel.key,
                    'target': rel.target.name,
                    'direction': rel.direction.name,
                    'foreign_keys': [],
                    'issues': []
                }

                # Get relationship's foreign keys
                fk_cols = list(rel.local_columns)
                if fk_cols:
                    for fk_col in fk_cols:
                        fk_col_name = fk_col.name
                        rel_info['foreign_keys'].append(fk_col_name)

                        # Check if foreign key column exists in database
                        if table_name in self.metadata.tables:
                            table = self.metadata.tables[table_name]
                            if fk_col_name not in table.columns:
                                issue = f"Foreign key column '{fk_col_name}' used in relationship {rel.key} doesn't exist in table {table_name}"
                                logger.warning(issue)
                                rel_info['issues'].append(issue)
                                self.results['foreign_key_issues'].append(issue)

                                # Add suggestion
                                suggestion = f"Add column '{fk_col_name}' to table '{table_name}' with foreign key reference to {rel.target.name}"
                                self.results['suggestions'].append(suggestion)

                # Check if relationship has a matching foreign key in database
                if db_fks and fk_cols:
                    fk_col_names = [c.name for c in fk_cols]
                    db_fk_cols = [fk['constrained_columns'] for fk in db_fks]
                    db_fk_cols_flat = [col for cols in db_fk_cols for col in cols]

                    for fk_col_name in fk_col_names:
                        if fk_col_name not in db_fk_cols_flat:
                            issue = f"No matching foreign key in database for relationship {rel.key} column {fk_col_name}"
                            logger.warning(issue)
                            rel_info['issues'].append(issue)
                            self.results['foreign_key_issues'].append(issue)

                            # Find target column
                            target_col = None
                            for fk_col in fk_cols:
                                if fk_col.name == fk_col_name:
                                    for ref in fk_col.foreign_keys:
                                        target_col = ref.column.name

                            # Add suggestion
                            if target_col:
                                suggestion = f"Add foreign key constraint on '{table_name}.{fk_col_name}' referencing '{rel.target.name}.{target_col}'"
                                self.results['suggestions'].append(suggestion)

                # Add to results
                if 'relationships' not in self.results['tables'][table_name]:
                    self.results['tables'][table_name]['relationships'] = []

                self.results['tables'][table_name]['relationships'].append(rel_info)

                # Add to relationship issues if any issues were found
                if rel_info['issues']:
                    self.results['relationship_issues'].append({
                        'model': model_class.__name__,
                        'table': table_name,
                        'relationship': rel.key,
                        'issues': rel_info['issues']
                    })

        except Exception as e:
            logger.error(f"Error analyzing relationships for {model_class.__name__}: {str(e)}")

    def _generate_report(self):
        """Generate a human-readable report of the analysis."""
        report = []
        report.append("=" * 80)
        report.append("DATABASE SCHEMA ANALYSIS REPORT")
        report.append("=" * 80)

        # Tables summary
        report.append("\nTABLES SUMMARY:")
        report.append(f"Tables in database: {len([t for t in self.results['tables'].values() if t['in_database']])}")
        report.append(f"Tables in models: {len([t for t in self.results['tables'].values() if t['in_models']])}")
        report.append(f"Missing tables (in models but not in database): {len(self.results['missing_tables'])}")
        report.append(f"Extra tables (in database but not in models): {len(self.results['extra_tables'])}")

        # Relationship and foreign key issues
        if self.results['relationship_issues']:
            report.append("\nRELATIONSHIP ISSUES:")
            for issue in self.results['relationship_issues']:
                report.append(
                    f"- Model {issue['model']} (table {issue['table']}), relationship {issue['relationship']}:")
                for sub_issue in issue['issues']:
                    report.append(f"  - {sub_issue}")

        if self.results['foreign_key_issues']:
            report.append("\nFOREIGN KEY ISSUES:")
            for issue in self.results['foreign_key_issues']:
                report.append(f"- {issue}")

        # Suggestions
        if self.results['suggestions']:
            report.append("\nSUGGESTIONS:")
            for suggestion in self.results['suggestions']:
                report.append(f"- {suggestion}")

        # Write report to file
        with open('schema_analysis_report.txt', 'w') as f:
            f.write('\n'.join(report))

        logger.info("Report written to schema_analysis_report.txt")


def main():
    """Run the schema analyzer."""
    analyzer = SchemaAnalyzer()
    results = analyzer.analyze()

    # Print summary
    print("\nSummary of database schema analysis:")
    print(f"Tables in database: {len([t for t in results['tables'].values() if t['in_database']])}")
    print(f"Tables in models: {len([t for t in results['tables'].values() if t['in_models']])}")
    print(f"Missing tables: {len(results['missing_tables'])}")
    print(f"Extra tables: {len(results['extra_tables'])}")
    print(f"Relationship issues: {len(results['relationship_issues'])}")
    print(f"Foreign key issues: {len(results['foreign_key_issues'])}")
    print(f"Suggestions: {len(results['suggestions'])}")
    print("\nSee schema_analysis_report.txt for full details.")


if __name__ == "__main__":
    main()
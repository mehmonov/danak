import os
import json
from datetime import datetime
from typing import Dict, List, Type
import sqlite3

class MigrationManager:
    def __init__(self, connection: sqlite3.Connection, migrations_dir: str = 'migrations'):
        self.connection = connection
        self.migrations_dir = migrations_dir
        self._ensure_migrations_table()
        self._ensure_migrations_directory()

    def _ensure_migrations_table(self):
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.connection.commit()

    def _ensure_migrations_directory(self):
        if not os.path.exists(self.migrations_dir):
            os.makedirs(self.migrations_dir)

    def create_migration(self, name: str, models: List[Type]) -> str:
        """Create a new migration file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{name}.json"
        filepath = os.path.join(self.migrations_dir, filename)

        operations = []
        for model in models:
            table_name = model._get_table_name()
            fields = {}
            for field_name, field in model._fields.items():
                field_def = {
                    'type': field.__class__.__name__,
                    'nullable': field.nullable,
                    'unique': field.unique,
                    'validators': []
                }
                if field.primary_key:
                    field_def['primary_key'] = True
                if hasattr(field, 'to_model'):
                    field_def['to_model'] = field.to_model
                    field_def['on_delete'] = field.on_delete
                if field.validators:
                    field_def['validators'] = [
                        {
                            'type': validator.__class__.__name__,
                            'args': validator.__dict__
                        }
                        for validator in field.validators
                    ]
                fields[field_name] = field_def

            operations.append({
                'type': 'create_table',
                'table': table_name,
                'fields': fields
            })

        with open(filepath, 'w') as f:
            json.dump({'operations': operations}, f, indent=2)

        return filename

    def apply_migrations(self) -> List[str]:
        """Apply all pending migrations"""
        applied = []
        for filename in sorted(os.listdir(self.migrations_dir)):
            if not filename.endswith('.json'):
                continue

            # Check if migration was already applied
            cursor = self.connection.execute(
                "SELECT 1 FROM migrations WHERE name = ?", (filename,))
            if cursor.fetchone():
                continue

            # Read and apply migration
            filepath = os.path.join(self.migrations_dir, filename)
            with open(filepath, 'r') as f:
                migration = json.load(f)

            for operation in migration['operations']:
                if operation['type'] == 'create_table':
                    self._create_table(operation)
                elif operation['type'] == 'alter_table':
                    self._alter_table(operation)
                elif operation['type'] == 'drop_table':
                    self._drop_table(operation)

            # Mark migration as applied
            self.connection.execute(
                "INSERT INTO migrations (name) VALUES (?)", (filename,))
            self.connection.commit()
            applied.append(filename)

        return applied

    def _create_table(self, operation: Dict):
        table_name = operation['table']
        fields = []
        for name, field in operation['fields'].items():
            field_def = f"{name} {self._get_field_type(field)}"
            if field.get('primary_key'):
                field_def += " PRIMARY KEY"
            if not field.get('nullable', True):
                field_def += " NOT NULL"
            if field.get('unique'):
                field_def += " UNIQUE"
            if 'to_model' in field:
                ref_table = field['to_model'].lower()
                field_def += f" REFERENCES {ref_table}(id)"
                if field.get('on_delete'):
                    field_def += f" ON DELETE {field['on_delete']}"
            fields.append(field_def)

        query = f"CREATE TABLE {table_name} ({', '.join(fields)})"
        self.connection.execute(query)

    def _alter_table(self, operation: Dict):
        table_name = operation['table']
        if 'add_field' in operation:
            for name, field in operation['add_field'].items():
                field_def = f"{name} {self._get_field_type(field)}"
                if not field.get('nullable', True):
                    if field['type'] == 'IntegerField':
                        field_def += " NOT NULL DEFAULT 0"
                    elif field['type'] == 'TextField':
                        field_def += " NOT NULL DEFAULT ''"
                    elif field['type'] == 'FloatField':
                        field_def += " NOT NULL DEFAULT 0.0"
                    elif field['type'] == 'BooleanField':
                        field_def += " NOT NULL DEFAULT 0"
                    elif field['type'] == 'DateTimeField':
                        field_def += " NOT NULL DEFAULT CURRENT_TIMESTAMP"
                    else:
                        field_def += " NOT NULL"
                query = f"ALTER TABLE {table_name} ADD COLUMN {field_def}"
                self.connection.execute(query)

    def _drop_table(self, operation: Dict):
        table_name = operation['table']
        self.connection.execute(f"DROP TABLE IF EXISTS {table_name}")

    def _get_field_type(self, field: Dict) -> str:
        type_mapping = {
            'IntegerField': 'INTEGER',
            'TextField': 'TEXT',
            'FloatField': 'REAL',
            'BooleanField': 'INTEGER',
            'DateTimeField': 'TIMESTAMP',
            'ForeignKey': 'INTEGER'
        }
        return type_mapping.get(field['type'], 'TEXT')

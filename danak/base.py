from typing import Any, Dict, List, Type, TypeVar, Optional
import sqlite3
from datetime import datetime
from .fields import Field, ForeignKey
from .query import QuerySet
from .validators import ValidationError

T = TypeVar('T', bound='Model')

class ModelMeta(type):
    def __new__(mcs, name: str, bases: tuple, attrs: dict):
        fields = {}
        for key, value in attrs.items():
            if isinstance(value, Field):
                value.name = key
                fields[key] = value
        
        attrs['_fields'] = fields
        return super().__new__(mcs, name, bases, attrs)

class Model(metaclass=ModelMeta):
    class DoesNotExist(Exception):
        pass

    class MultipleObjectsReturned(Exception):
        pass

    _connection: sqlite3.Connection = None
    _table_name: str = None
    _fields: Dict[str, Field] = {}

    @classmethod
    def connect(cls, db_path: str):
        cls._connection = sqlite3.connect(db_path)
        cls._connection.row_factory = sqlite3.Row

    @classmethod
    def create_table(cls):
        if not cls._connection:
            raise Exception("Database connection not established")

        fields = []
        for name, field in cls._fields.items():
            field_def = f"{name} {cls._get_sql_type(field.field_type)}"
            if field.primary_key:
                field_def += " PRIMARY KEY"
            if not field.nullable:
                field_def += " NOT NULL"
            if field.unique:
                field_def += " UNIQUE"
            if hasattr(field, 'to_model'):
                ref_table = field.to_model.lower()
                field_def += f" REFERENCES {ref_table}(id)"
                if field.on_delete:
                    field_def += f" ON DELETE {field.on_delete}"
            fields.append(field_def)

        query = f"CREATE TABLE IF NOT EXISTS {cls._get_table_name()} ({', '.join(fields)})"
        cls._connection.execute(query)
        cls._connection.commit()

    @classmethod
    def _get_table_name(cls) -> str:
        return cls._table_name or cls.__name__.lower()

    @staticmethod
    def _get_sql_type(python_type: type) -> str:
        type_mapping = {
            int: "INTEGER",
            str: "TEXT",
            float: "REAL",
            bool: "INTEGER",
            datetime: "TIMESTAMP"
        }
        return type_mapping.get(python_type, "TEXT")

    def __init__(self, **kwargs):
        self._data = {}
        for key, value in kwargs.items():
            if key in self._fields:
                setattr(self, key, value)

    def __getattr__(self, name):
        if name in self._data:
            value = self._data[name]
            # Handle foreign key lazy loading
            if isinstance(self._fields[name], ForeignKey) and isinstance(value, dict) and not value.get('_loaded'):
                ref_model = self._get_model_class(self._fields[name].to_model)
                value = ref_model.get(id=value['id'])
                self._data[name] = value
            return value
        return super().__getattribute__(name)

    def __setattr__(self, name, value):
        if name == '_data':
            super().__setattr__(name, value)
        elif name in getattr(self, '_fields', {}):
            field = self._fields[name]
            field.validate(value)
            self._data[name] = field.to_db_value(value)
        else:
            super().__setattr__(name, value)

    def __str__(self):
        values = []
        for name in self._fields:
            value = self._data.get(name, None)
            values.append(f"{name}={value}")
        return f"{self.__class__.__name__}({', '.join(values)})"

    def __repr__(self):
        return self.__str__()

    def save(self) -> None:
        if not self._connection:
            raise Exception("Database connection not established")

        # Validate all fields
        for name, field in self._fields.items():
            value = self._data.get(name)
            field.validate(value)

        fields = []
        values = []
        placeholders = []

        for name, field in self._fields.items():
            if name in self._data:
                value = field.to_db_value(self._data[name])
                fields.append(name)
                values.append(value)
                placeholders.append('?')

        query = f"INSERT OR REPLACE INTO {self._get_table_name()} ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"
        cursor = self._connection.execute(query, values)
        self._connection.commit()
        
        # Update primary key if it was auto-generated
        if 'id' in self._fields and 'id' not in self._data:
            self._data['id'] = cursor.lastrowid

    @classmethod
    def filter(cls: Type[T], **kwargs) -> QuerySet[T]:
        return QuerySet(cls).filter(**kwargs)

    @classmethod
    def exclude(cls: Type[T], **kwargs) -> QuerySet[T]:
        return QuerySet(cls).exclude(**kwargs)

    @classmethod
    def get(cls: Type[T], **kwargs) -> T:
        return QuerySet(cls).get(**kwargs)

    @classmethod
    def all(cls: Type[T]) -> QuerySet[T]:
        return QuerySet(cls)

    @classmethod
    def create(cls, **kwargs) -> 'Model':
        instance = cls(**kwargs)
        instance.save()
        return instance

    def update(self, **kwargs) -> None:
        if not self._connection:
            raise Exception("Database connection not established")

        updates = []
        values = []
        for key, value in kwargs.items():
            if key in self._fields:
                field = self._fields[key]
                field.validate(value)
                db_value = field.to_db_value(value)
                updates.append(f"{key} = ?")
                values.append(db_value)
                self._data[key] = value

        # Get primary key for WHERE clause
        pk_field = next((name for name, field in self._fields.items() if field.primary_key), None)
        if not pk_field:
            raise Exception("No primary key field defined")

        pk_value = self._data.get(pk_field)
        if pk_value is None:
            raise Exception("Primary key value not found")
            
        values.append(pk_value)

        query = f"UPDATE {self._get_table_name()} SET {', '.join(updates)} WHERE {pk_field} = ?"
        self._connection.execute(query, values)
        self._connection.commit()

    def delete(self) -> None:
        if not self._connection:
            raise Exception("Database connection not established")

        pk_field = next((name for name, field in self._fields.items() if field.primary_key), None)
        if not pk_field:
            raise Exception("No primary key field defined")

        pk_value = self._data.get(pk_field)
        if pk_value is None:
            raise Exception("Primary key value not found")

        query = f"DELETE FROM {self._get_table_name()} WHERE {pk_field} = ?"
        self._connection.execute(query, (pk_value,))
        self._connection.commit()

    @classmethod
    def _get_model_class(cls, model_name: str) -> Type['Model']:
        """Get model class by name"""
        for subclass in cls.__subclasses__():
            if subclass.__name__.lower() == model_name.lower():
                return subclass
        raise ValueError(f"Model {model_name} not found")

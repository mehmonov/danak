from typing import Any, Dict, List, Optional, Type, TypeVar, Union, Generic
from datetime import datetime

T = TypeVar('T')

class QuerySet(Generic[T]):
    def __init__(self, model_class: Type[T], conditions: List = None, 
                 order_by: List = None, limit: int = None, offset: int = None):
        self.model_class = model_class
        self.conditions = conditions or []
        self.order_by = order_by or []
        self.limit = limit
        self.offset = offset
        self._results = None
        self._count = None

    def filter(self, **kwargs) -> 'QuerySet[T]':
        new_conditions = self.conditions.copy()
        for key, value in kwargs.items():
            if '__' in key:
                field, op = key.split('__')
                new_conditions.append((field, self._get_operator(op), value))
            else:
                new_conditions.append((key, '=', value))
        return QuerySet(self.model_class, new_conditions, self.order_by, 
                       self.limit, self.offset)

    def exclude(self, **kwargs) -> 'QuerySet[T]':
        new_conditions = self.conditions.copy()
        for key, value in kwargs.items():
            if '__' in key:
                field, op = key.split('__')
                new_conditions.append((field, self._get_not_operator(op), value))
            else:
                new_conditions.append((key, '!=', value))
        return QuerySet(self.model_class, new_conditions, self.order_by,
                       self.limit, self.offset)

    def order_by_fields(self, *fields) -> 'QuerySet[T]':
        new_order = self.order_by.copy()
        for field in fields:
            if field.startswith('-'):
                new_order.append((field[1:], 'DESC'))
            else:
                new_order.append((field, 'ASC'))
        return QuerySet(self.model_class, self.conditions, new_order,
                       self.limit, self.offset)

    def limit(self, num: int) -> 'QuerySet[T]':
        return QuerySet(self.model_class, self.conditions, self.order_by,
                       num, self.offset)

    def offset(self, num: int) -> 'QuerySet[T]':
        return QuerySet(self.model_class, self.conditions, self.order_by,
                       self.limit, num)

    def count(self) -> int:
        if self._count is None:
            query = self._build_query(count=True)
            cursor = self.model_class._connection.execute(query[0], query[1])
            self._count = cursor.fetchone()[0]
        return self._count

    def exists(self) -> bool:
        return self.count() > 0

    def get(self, **kwargs) -> T:
        if kwargs:
            qs = self.filter(**kwargs)
        else:
            qs = self

        results = list(qs)
        if not results:
            raise self.model_class.DoesNotExist()
        if len(results) > 1:
            raise self.model_class.MultipleObjectsReturned()
        return results[0]

    def first(self) -> Optional[T]:
        qs = self.limit(1)
        try:
            return list(qs)[0]
        except IndexError:
            return None

    def last(self) -> Optional[T]:
        if not self.order_by:
            qs = self.order_by_fields('-id')
        else:
            new_order = []
            for field, direction in self.order_by:
                new_order.append((field, 'DESC' if direction == 'ASC' else 'ASC'))
            qs = QuerySet(self.model_class, self.conditions, new_order,
                         1, self.offset)
        return qs.first()

    def _build_query(self, count: bool = False) -> tuple:
        params = []
        where_clauses = []

        for field, op, value in self.conditions:
            if isinstance(value, (list, tuple)):
                placeholders = ', '.join(['?' for _ in value])
                where_clauses.append(f"{field} {op} ({placeholders})")
                params.extend(value)
            else:
                where_clauses.append(f"{field} {op} ?")
                params.append(value)

        where_clause = ' AND '.join(where_clauses) if where_clauses else '1=1'
        
        if count:
            query = f"SELECT COUNT(*) FROM {self.model_class._get_table_name()} WHERE {where_clause}"
        else:
            query = f"SELECT * FROM {self.model_class._get_table_name()} WHERE {where_clause}"
            
            if self.order_by:
                order_clauses = [f"{field} {direction}" for field, direction in self.order_by]
                query += f" ORDER BY {', '.join(order_clauses)}"
            
            if self.limit is not None:
                query += f" LIMIT {self.limit}"
            
            if self.offset is not None:
                query += f" OFFSET {self.offset}"

        return query, params

    def _get_operator(self, op: str) -> str:
        operators = {
            'lt': '<',
            'lte': '<=',
            'gt': '>',
            'gte': '>=',
            'in': 'IN',
            'contains': 'LIKE',
            'startswith': 'LIKE',
            'endswith': 'LIKE',
            'range': 'BETWEEN',
            'isnull': 'IS' if True else 'IS NOT'
        }
        return operators.get(op, '=')

    def _get_not_operator(self, op: str) -> str:
        operators = {
            'lt': '>=',
            'lte': '>',
            'gt': '<=',
            'gte': '<',
            'in': 'NOT IN',
            'contains': 'NOT LIKE',
            'startswith': 'NOT LIKE',
            'endswith': 'NOT LIKE',
            'range': 'NOT BETWEEN',
            'isnull': 'IS NOT' if True else 'IS'
        }
        return operators.get(op, '!=')

    def __iter__(self):
        if self._results is None:
            query = self._build_query()
            cursor = self.model_class._connection.execute(query[0], query[1])
            rows = cursor.fetchall()
            self._results = []
            for row in rows:
                instance = self.model_class()
                for key in row.keys():
                    if key in self.model_class._fields:
                        field = self.model_class._fields[key]
                        value = field.to_python_value(row[key])
                        instance._data[key] = value
                self._results.append(instance)
        return iter(self._results)

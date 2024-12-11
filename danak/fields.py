from typing import Any, List, Type, Optional
from datetime import datetime
from .validators import (ValidationError, Validator, MinValueValidator,
                      MaxValueValidator, MaxLengthValidator)

class Field:
    def __init__(self, field_type: type, primary_key: bool = False, 
                 nullable: bool = True, unique: bool = False,
                 validators: List[Validator] = None):
        self.field_type = field_type
        self.primary_key = primary_key
        self.nullable = nullable
        self.unique = unique
        self.validators = validators or []
        self.name = None  # Will be set by Model metaclass

    def validate(self, value: Any) -> None:
        if value is None:
            if not self.nullable:
                raise ValidationError(f"{self.name} cannot be null")
            return

        if not isinstance(value, self.field_type):
            try:
                value = self.field_type(value)
            except (ValueError, TypeError):
                raise ValidationError(f"{self.name} must be of type {self.field_type.__name__}")

        for validator in self.validators:
            validator.validate(value)

    def to_db_value(self, value: Any) -> Any:
        """Convert Python value to database value"""
        if value is None:
            return None
        return value

    def to_python_value(self, value: Any) -> Any:
        """Convert database value to Python value"""
        if value is None:
            return None
        return value

class IntegerField(Field):
    def __init__(self, primary_key: bool = False, nullable: bool = True,
                 unique: bool = False, validators: List[Validator] = None,
                 min_value: Optional[int] = None, max_value: Optional[int] = None):
        super().__init__(int, primary_key, nullable, unique, validators)
        if min_value is not None:
            self.validators.append(MinValueValidator(min_value))
        if max_value is not None:
            self.validators.append(MaxValueValidator(max_value))

class FloatField(Field):
    def __init__(self, nullable: bool = True, unique: bool = False,
                 validators: List[Validator] = None,
                 min_value: Optional[float] = None, max_value: Optional[float] = None):
        super().__init__(float, False, nullable, unique, validators)
        if min_value is not None:
            self.validators.append(MinValueValidator(min_value))
        if max_value is not None:
            self.validators.append(MaxValueValidator(max_value))

class TextField(Field):
    def __init__(self, nullable: bool = True, unique: bool = False,
                 validators: List[Validator] = None, max_length: Optional[int] = None):
        super().__init__(str, False, nullable, unique, validators)
        if max_length is not None:
            self.validators.append(MaxLengthValidator(max_length))

class BooleanField(Field):
    def __init__(self, nullable: bool = True, validators: List[Validator] = None):
        super().__init__(bool, False, nullable, False, validators)

    def to_db_value(self, value: bool) -> int:
        if value is None:
            return None
        return 1 if value else 0

    def to_python_value(self, value: Any) -> bool:
        if value is None:
            return None
        return bool(value)

class DateTimeField(Field):
    def __init__(self, nullable: bool = True, auto_now: bool = False,
                 auto_now_add: bool = False, validators: List[Validator] = None):
        super().__init__(datetime, False, nullable, False, validators)
        self.auto_now = auto_now
        self.auto_now_add = auto_now_add
        self._set = False

    def to_db_value(self, value: datetime) -> str:
        if value is None:
            if self.auto_now or (self.auto_now_add and not self._set):
                value = datetime.now()
                self._set = True
            else:
                return None
        return value.isoformat()

    def to_python_value(self, value: str) -> datetime:
        if value is None:
            return None
        return datetime.fromisoformat(value)

class ForeignKey(Field):
    def __init__(self, to_model: str, nullable: bool = True,
                 on_delete: str = 'CASCADE', validators: List[Validator] = None):
        super().__init__(int, False, nullable, False, validators)
        self.to_model = to_model
        self.on_delete = on_delete.upper()
        if self.on_delete not in ['CASCADE', 'SET_NULL', 'PROTECT']:
            raise ValueError("on_delete must be one of: CASCADE, SET_NULL, PROTECT")

    def to_db_value(self, value: Any) -> int:
        if isinstance(value, dict) and 'id' in value:
            return value['id']
        return value

    def to_python_value(self, value: int) -> Any:
        if value is None:
            return None
        # Lazy loading will be handled by the Model class
        return {'id': value, '_loaded': False}

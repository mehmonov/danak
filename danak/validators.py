from typing import Any

class ValidationError(Exception):
    pass

class Validator:
    def validate(self, value: Any) -> None:
        raise NotImplementedError

class MinValueValidator(Validator):
    def __init__(self, min_value: Any):
        self.min_value = min_value

    def validate(self, value: Any) -> None:
        if value < self.min_value:
            raise ValidationError(f"Value must be greater than or equal to {self.min_value}")

class MaxValueValidator(Validator):
    def __init__(self, max_value: Any):
        self.max_value = max_value

    def validate(self, value: Any) -> None:
        if value > self.max_value:
            raise ValidationError(f"Value must be less than or equal to {self.max_value}")

class MinLengthValidator(Validator):
    def __init__(self, min_length: int):
        self.min_length = min_length

    def validate(self, value: Any) -> None:
        if len(value) < self.min_length:
            raise ValidationError(f"Length must be greater than or equal to {self.min_length}")

class MaxLengthValidator(Validator):
    def __init__(self, max_length: int):
        self.max_length = max_length

    def validate(self, value: Any) -> None:
        if len(value) > self.max_length:
            raise ValidationError(f"Length must be less than or equal to {self.max_length}")

class RegexValidator(Validator):
    def __init__(self, pattern: str, message: str = None):
        import re
        self.pattern = re.compile(pattern)
        self.message = message or f"Value does not match pattern {pattern}"

    def validate(self, value: Any) -> None:
        if not self.pattern.match(str(value)):
            raise ValidationError(self.message)

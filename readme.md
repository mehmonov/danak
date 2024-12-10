# Danak - Lightweight Python ORM

## 🚀 Project Overview

Danak is a simple and flexible Object-Relational Mapping (ORM) library for Python. This library simplifies database interactions and provides an intuitive interface for Python developers.

## ✨ Key Features

- **Easy Model Creation**: Quickly and effortlessly create database models
- **Migration Management**: Convenient migration mechanism for managing database structures
- **Flexible Field Handling**: Support for various data field types
- **Minimal Configuration**: Quick setup with minimal configuration required
- **Convenient Sorting and Filtering**: Easy data sorting and filtering capabilities

## 🛠️ Technologies

- Programming Language: Python
- ORM Type: Lightweight
- Database Compatibility: Works with SQL databases like SQLite, PostgreSQL, MySQL

## 📦 Installation

```bash
pip install danak
```

## 🚦 Basic Usage Examples

### Creating a Model
```python
from danak import Model, Field

class User(Model):
    id = Field(int, primary_key=True)
    name = Field(str)
    email = Field(str, unique=True)
```

### Creating Migrations
```python
from danak import create_migrations

create_migrations(User)
```

## 🤝 Contributing

Contributions are welcome! Feel free to open pull requests or issues.

## 📄 License

MIT License

## 📬 Contact

For questions and suggestions, please use the GitHub issues section.

---
sidebar_position: 3
---

# Quick Start Guide

## Creating Your First Model

To create your first model with Danak, follow these steps:

1. **Define a Model**: Create a Python class that inherits from `danak.Model`.

```python
from danak.base import Model
from danak.fields import IntegerField, TextField

class User(Model):
    id = IntegerField(primary_key=True)
    username = TextField(nullable=False, unique=True)
```

2. **Connect to a Database**: Establish a connection to your SQLite database.

```python
User.connect('my_database.db')
```

3. **Create a Table**: Generate the corresponding table in the database.

```python
User.create_table()
```

4. **Perform CRUD Operations**: Use the model to perform create, read, update, and delete operations.

```python
# Create a new user
user = User.create(username='john_doe')

# Read users
users = User.all()

# Update a user
user.username = 'jane_doe'
user.save()

# Delete a user
user.delete()
```

This quick start guide demonstrates the basic usage of Danak to define models and interact with a database.

---
sidebar_position: 1
---

# Advanced Usage

## Custom Queries

Danak allows you to create custom queries using the `QuerySet` class. You can filter, order, and aggregate data with ease.

```python
# Filter users by username
users = User.filter(username__contains='john')

# Order users by ID
users = User.order_by_fields('-id')
```

## Handling Relationships

Danak supports relationships between models, such as one-to-many and many-to-many.

```python
from danak.fields import ForeignKey

class Post(Model):
    author = ForeignKey('User', nullable=False, on_delete='CASCADE')
```

## Migrations

To handle database schema changes, Danak provides a migration system.

```python
from danak.migrations import MigrationManager

manager = MigrationManager(User._connection)
manager.create_migration('add_new_field', [User])
manager.apply_migrations()
```

## Performance Optimization

For better performance, consider using indexing and optimizing your queries.

```python
# Create an index on the username field
User._connection.execute('CREATE INDEX idx_username ON user (username)')
```

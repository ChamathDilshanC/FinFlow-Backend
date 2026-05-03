"""
Declarative base for SQLAlchemy ORM models.

All mapped classes inherit from :class:`Base` for a single metadata registry.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Root declarative base shared by all ORM tables."""

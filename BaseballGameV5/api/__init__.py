"""
API module for baseball game simulation.

Exports:
- app: FastAPI application
- models: Pydantic models for request/response validation
"""

from .app import app
from . import models

__all__ = ["app", "models"]

"""Pytest configuration and global fixtures."""

from __future__ import annotations

import os
import tempfile

import pytest

from app.common.middleware import _rate_limit_store
from app.config import settings
import app.database

_test_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_test_db.close()
settings.database_path = _test_db.name
app.database.DB_PATH = _test_db.name


@pytest.fixture(autouse=True)
def clear_rate_limit():
    _rate_limit_store.clear()

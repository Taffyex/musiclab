import pytest
from app.common.middleware import _rate_limit_store

@pytest.fixture(autouse=True)
def clear_rate_limit():
    _rate_limit_store.clear()

import pytest

from app import app

__all__ = ("client",)


@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client

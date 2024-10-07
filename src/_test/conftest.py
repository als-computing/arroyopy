from unittest.mock import MagicMock, AsyncMock

import pytest


@pytest.fixture
def operator_mock():
    return AsyncMock()


@pytest.fixture
def publisher_mock():
    return AsyncMock()

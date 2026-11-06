"""Only the integration's client boundary is mocked."""

from unittest.mock import AsyncMock, patch

import pytest

from custom_components.loseit.client import Account, DailySnapshot


@pytest.fixture
def client():
    with (
        patch("custom_components.loseit.config_flow.LoseItClient") as flow,
        patch("custom_components.loseit.LoseItClient") as setup,
    ):
        api = AsyncMock()
        api.async_get_account.return_value = Account("synthetic-account", "UTC")
        api.async_get_day.side_effect = lambda day: DailySnapshot(day, food_kcal=0)
        flow.return_value = setup.return_value = api
        yield api

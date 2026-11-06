"""Real HA platform states expose explicit icons, including optional entities."""

from decimal import Decimal

import pytest
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.loseit.client import DailySnapshot, LoseItConnectionError

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")

EXPECTED_ICONS = {
    "budget_kcal": "mdi:fire-circle",
    "food_kcal": "mdi:food-apple",
    "exercise_kcal": "mdi:run",
    "net_kcal": "mdi:calculator",
    "remaining_kcal": "mdi:fire",
    "protein_g": "mdi:food-steak",
    "carbohydrates_g": "mdi:bread-slice",
    "fat_g": "mdi:water",
    "weight_kg": "mdi:scale-bathroom",
    "goal_weight_kg": "mdi:flag-checkered",
    "logged_food_count": "mdi:format-list-numbered",
    "day": "mdi:calendar-today",
    "last_success": "mdi:update",
}
OPTIONAL = {"protein_g", "carbohydrates_g", "fat_g", "logged_food_count"}


# Existing public identities and state semantics, independent of sensor descriptions.
# key: (entity ID suffix, populated state, unit, device class)
EXPECTED_STATES = {
    "budget_kcal": ("calorie_budget", "2000", "kcal", None),
    "food_kcal": ("food_calories", "0", "kcal", None),
    "exercise_kcal": ("exercise_calories", "unknown", "kcal", None),
    "net_kcal": ("net_calories", "unknown", "kcal", None),
    "remaining_kcal": ("remaining_calories", "unknown", "kcal", None),
    "protein_g": ("protein", "12.5", "g", None),
    "carbohydrates_g": ("carbohydrates", "30", "g", None),
    "fat_g": ("fat", "0", "g", None),
    "weight_kg": ("recorded_weight_for_diary_day", "80", "kg", "weight"),
    "goal_weight_kg": ("goal_weight", "75", "kg", "weight"),
    "logged_food_count": ("logged_food_count", "0", None, None),
    "day": ("source_diary_date", "2026-01-15", None, "date"),
    "last_success": (
        "last_successful_refresh",
        "2026-01-15T12:00:00+00:00",
        None,
        "timestamp",
    ),
}


async def test_all_sensor_icons_in_real_ha_states(hass, client, freezer):
    """Only provider I/O is mocked; enable optional sensors through HA registry."""
    freezer.move_to("2026-01-15T12:00:00Z")
    client.async_get_day.side_effect = lambda day: DailySnapshot(
        day,
        budget_kcal=Decimal("2000"),
        food_kcal=Decimal("0"),
        protein_g=Decimal("12.5"),
        carbohydrates_g=Decimal("30"),
        fat_g=Decimal("0"),
        weight_kg=Decimal("80"),
        goal_weight_kg=Decimal("75"),
        logged_food_count=0,
    )
    item = MockConfigEntry(
        domain="loseit",
        unique_id="synthetic-account",
        data={
            "cookies": {"session": "synthetic-secret"},
            "timezone": "UTC",
            "source_timezone": "UTC",
        },
        title="Lose It!",
    )
    item.add_to_hass(hass)
    assert await hass.config_entries.async_setup(item.entry_id)
    await hass.async_block_till_done()
    registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(registry, item.entry_id)
    assert {entity.unique_id for entity in entries} == {
        f"synthetic-account_{key}" for key in EXPECTED_ICONS
    }
    for key in EXPECTED_ICONS:
        entity_id = registry.async_get_entity_id(
            "sensor", "loseit", f"synthetic-account_{key}"
        )
        assert entity_id is not None
        entity = registry.async_get(entity_id)
        assert entity is not None
        if key in OPTIONAL:
            assert entity.disabled_by is er.RegistryEntryDisabler.INTEGRATION
            assert hass.states.get(entity_id) is None
            registry.async_update_entity(entity_id, disabled_by=None)
        else:
            assert entity.disabled_by is None
    # Reload explicitly rather than depending on the registry's delayed reload.
    assert await hass.config_entries.async_reload(item.entry_id)
    await hass.async_block_till_done()
    for key, icon in EXPECTED_ICONS.items():
        entity_id = registry.async_get_entity_id(
            "sensor", "loseit", f"synthetic-account_{key}"
        )
        suffix, value, unit, device_class = EXPECTED_STATES[key]
        assert entity_id == f"sensor.lose_it_{suffix}", key
        state = hass.states.get(entity_id)
        assert state is not None, key
        assert state.state == value, key
        assert state.attributes["icon"] == icon, key
        assert state.attributes.get("unit_of_measurement") == unit, key
        assert state.attributes.get("device_class") == device_class, key
        assert "state_class" not in state.attributes, key
    # Branding must not turn a provider failure into unknown or a numeric zero.
    client.async_get_day.side_effect = LoseItConnectionError()
    await item.runtime_data.async_refresh()
    for key, (suffix, _, unit, device_class) in EXPECTED_STATES.items():
        state = hass.states.get(f"sensor.lose_it_{suffix}")
        assert state.state == "unavailable", key
        assert state.attributes["icon"] == EXPECTED_ICONS[key], key
        assert state.attributes.get("unit_of_measurement") == unit, key
        assert state.attributes.get("device_class") == device_class, key
    assert await hass.config_entries.async_unload(item.entry_id)
    await hass.async_block_till_done()

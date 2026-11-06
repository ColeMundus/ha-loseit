"""Read-only sensors; entity properties perform no I/O."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.const import EntityCategory, UnitOfMass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import LoseItConfigEntry
from .const import DOMAIN
from .coordinator import LoseItCoordinator


@dataclass(frozen=True, kw_only=True)
class LoseItSensorDescription(SensorEntityDescription):
    daily: bool = True


SENSORS = (
    LoseItSensorDescription(
        icon="mdi:fire-circle",
        key="budget_kcal",
        translation_key="budget_kcal",
        native_unit_of_measurement="kcal",
    ),
    LoseItSensorDescription(
        icon="mdi:food-apple",
        key="food_kcal",
        translation_key="food_kcal",
        native_unit_of_measurement="kcal",
    ),
    LoseItSensorDescription(
        icon="mdi:run",
        key="exercise_kcal",
        translation_key="exercise_kcal",
        native_unit_of_measurement="kcal",
    ),
    LoseItSensorDescription(
        icon="mdi:calculator",
        key="net_kcal",
        translation_key="net_kcal",
        native_unit_of_measurement="kcal",
    ),
    LoseItSensorDescription(
        icon="mdi:fire",
        key="remaining_kcal",
        translation_key="remaining_kcal",
        native_unit_of_measurement="kcal",
    ),
    *(
        LoseItSensorDescription(
            key=key,
            translation_key=key,
            icon=icon,
            native_unit_of_measurement="g",
            entity_registry_enabled_default=False,
        )
        for key, icon in (
            ("protein_g", "mdi:food-steak"),
            ("carbohydrates_g", "mdi:bread-slice"),
            ("fat_g", "mdi:water"),
        )
    ),
    LoseItSensorDescription(
        icon="mdi:scale-bathroom",
        key="weight_kg",
        translation_key="weight_kg",
        device_class=SensorDeviceClass.WEIGHT,
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
    ),
    LoseItSensorDescription(
        icon="mdi:flag-checkered",
        key="goal_weight_kg",
        translation_key="goal_weight_kg",
        daily=False,
        device_class=SensorDeviceClass.WEIGHT,
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
    ),
    LoseItSensorDescription(
        icon="mdi:format-list-numbered",
        key="logged_food_count",
        translation_key="logged_food_count",
        entity_registry_enabled_default=False,
    ),
    LoseItSensorDescription(
        icon="mdi:calendar-today",
        key="day",
        translation_key="day",
        device_class=SensorDeviceClass.DATE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    LoseItSensorDescription(
        icon="mdi:update",
        key="last_success",
        translation_key="last_success",
        daily=False,
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LoseItConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities(
        LoseItSensor(entry.runtime_data, entry, description) for description in SENSORS
    )


class LoseItSensor(CoordinatorEntity[LoseItCoordinator], SensorEntity):
    _attr_has_entity_name = True
    entity_description: LoseItSensorDescription

    def __init__(
        self,
        coordinator: LoseItCoordinator,
        entry: LoseItConfigEntry,
        description: LoseItSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.unique_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(entry.unique_id))},
            name="Lose It!",
            entry_type=DeviceEntryType.SERVICE,
            manufacturer="Lose It!",
        )

    @property
    def native_value(self) -> Decimal | float | int | date | datetime | None:
        key = self.entity_description.key
        if key == "last_success":
            return self.coordinator.last_success
        snapshot = self.coordinator.data
        if snapshot is None or (
            self.entity_description.daily
            and snapshot.day != self.coordinator.current_day
        ):
            return None
        return getattr(snapshot, key)

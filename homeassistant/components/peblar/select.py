"""Support for Peblar selects."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from peblar import Peblar, PeblarUserConfiguration, SmartChargingMode

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PeblarConfigEntry, PeblarUserConfigurationDataUpdateCoordinator

PARALLEL_UPDATES = 1


@dataclass(frozen=True, kw_only=True)
class PeblarSelectEntityDescription(SelectEntityDescription):
    """Class describing Peblar select entities."""

    current_fn: Callable[[PeblarUserConfiguration], str | None]
    select_fn: Callable[[Peblar, str], Awaitable[Any]]


DESCRIPTIONS = [
    PeblarSelectEntityDescription(
        key="smart_charging",
        translation_key="smart_charging",
        entity_category=EntityCategory.CONFIG,
        options=[
            "default",
            "fast_solar",
            "pure_solar",
            "scheduled",
            "smart_solar",
        ],
        current_fn=lambda x: x.smart_charging.value if x.smart_charging else None,
        select_fn=lambda x, mode: x.smart_charging(SmartChargingMode(mode)),
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PeblarConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Peblar select based on a config entry."""
    async_add_entities(
        PeblarSelectEntity(
            entry=entry,
            description=description,
        )
        for description in DESCRIPTIONS
    )


class PeblarSelectEntity(
    CoordinatorEntity[PeblarUserConfigurationDataUpdateCoordinator], SelectEntity
):
    """Defines a peblar select entity."""

    entity_description: PeblarSelectEntityDescription

    _attr_has_entity_name = True

    def __init__(
        self,
        entry: PeblarConfigEntry,
        description: PeblarSelectEntityDescription,
    ) -> None:
        """Initialize the select entity."""
        super().__init__(entry.runtime_data.user_configuraton_coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.unique_id}-{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={
                (DOMAIN, entry.runtime_data.system_information.product_serial_number)
            },
        )

    @property
    def current_option(self) -> str | None:
        """Return the selected entity option to represent the entity state."""
        return self.entity_description.current_fn(self.coordinator.data)

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self.entity_description.select_fn(self.coordinator.peblar, option)
        await self.coordinator.async_request_refresh()

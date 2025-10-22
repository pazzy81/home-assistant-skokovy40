"""Select entities for the Salus Controls device."""

from homeassistant.components.select import (
    SelectEntity
)
from homeassistant.const import EntityCategory

from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.core import callback

from homeassistant.const import (
    CONF_DEVICE_ID
)

from .const import (
    DOMAIN,
)

SPAN_VALUES = [
    "Hysteresis ±0.25°C",
    "Hysteresis ±0.5°C",
    "Hysteresis ±1.0°C",
    "Hysteresis ±1.5°C",
    "Hysteresis ±2.0°C"]


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Salus selects from a config entry."""

    coordinator = config_entry.runtime_data
    device_id = config_entry.data[CONF_DEVICE_ID]

    async_add_entities([
        TemperatureSpanEntity(
            "Temperature span", coordinator, coordinator.get_client, device_id)
    ])


class TemperatureSpanEntity(CoordinatorEntity, SelectEntity):
    """Select entity for temperature span."""
    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_options = SPAN_VALUES

    def __init__(self, name, coordinator, client, device_id):
        """Initialize the select."""
        super().__init__(coordinator)
        self._name = name
        self._device_id = device_id
        self._coordinator = coordinator
        self._client = client
        self._attr_unique_id = "_".join([self._device_id, "temperature_span"])

    @property
    def name(self):
        """Name of the entity."""
        return self._name

    @property
    def device_info(self):
        """Return information to link this entity with the correct device."""
        return {"identifiers": {(DOMAIN, self._device_id)}}

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        value = self.map_value(SPAN_VALUES.index(option))
        await self._client.set_temperature_span(value)
        await self._coordinator.async_request_refresh()

    @property
    def current_option(self) -> str | None:
        """Get the current status of the select entity from device_status."""
        if not isinstance(self.selected_value, int):
            return None
        else:
            return SPAN_VALUES[self.map_value(self.selected_value)]

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.selected_value = self._coordinator.data.temperature_span
        self.async_write_ha_state()

    def map_value(self, value: int) -> int:
        """API uses different value than index in the select list"""
        if value == 1:
            return 0
        elif value == 0:
            return 1
        else:
            return value

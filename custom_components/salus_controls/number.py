"""Number entities   for the Salus Controls device."""

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberMode
)
from homeassistant.const import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.core import callback

from homeassistant.const import (
    CONF_DEVICE_ID,
    UnitOfTemperature
)

from .const import (
    DOMAIN,
    FREEZE_PROTECTION_MIN_TEMP,
    FREEZE_PROTECTION_MAX_TEMP,
    TEMPERATURE_OFFSET_MAX,
    TEMPERATURE_OFFSET_MIN
)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Salus numbers from a config entry."""

    coordinator = config_entry.runtime_data
    device_id = config_entry.data[CONF_DEVICE_ID]

    async_add_entities([
        FreezeProtectionEntity(
            "Freeze protection temperature", coordinator, coordinator.get_client, device_id),
        TemperatureOffsetEntity(
            "Temperature offset", coordinator, coordinator.get_client, device_id)
    ])


class FreezeProtectionEntity(CoordinatorEntity, NumberEntity):
    """Number entity for freeze protection temperature."""
    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_icon = "mdi:snowflake-thermometer"
    _attr_mode = NumberMode.AUTO
    _attr_native_min_value = FREEZE_PROTECTION_MIN_TEMP
    _attr_native_max_value = FREEZE_PROTECTION_MAX_TEMP
    _attr_native_step = 0.5
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, name, coordinator, client, device_id):
        """Initialize the number."""
        super().__init__(coordinator)
        self._name = name
        self._device_id = device_id
        self._coordinator = coordinator
        self._client = client
        self._attr_unique_id = "_".join(
            [self._device_id, "freeze_protection_temperature"])

    @property
    def name(self):
        """Name of the entity."""
        return self._name

    @property
    def device_info(self):
        """Return information to link this entity with the correct device."""
        return {"identifiers": {(DOMAIN, self._device_id)}}

    async def async_set_native_value(self, value: float) -> None:
        """Set new freeze protection temperature value."""
        await self._client.set_freeze_protection_temperature(value)
        await self._coordinator.async_request_refresh()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_native_value = self._coordinator.data.frost
        self.async_write_ha_state()


class TemperatureOffsetEntity(CoordinatorEntity, NumberEntity):
    """Number entity for temperature offset."""
    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_icon = "mdi:thermometer-plus"
    _attr_mode = NumberMode.AUTO
    _attr_native_min_value = TEMPERATURE_OFFSET_MIN
    _attr_native_max_value = TEMPERATURE_OFFSET_MAX
    _attr_native_step = 0.5
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, name, coordinator, client, device_id):
        """Initialize the number."""
        super().__init__(coordinator)
        self._name = name
        self._device_id = device_id
        self._coordinator = coordinator
        self._client = client
        self._attr_unique_id = "_".join(
            [self._device_id, "temperature_offset"])

    @property
    def name(self):
        """Name of the entity."""
        return self._name

    @property
    def device_info(self):
        """Return information to link this entity with the correct device."""
        return {"identifiers": {(DOMAIN, self._device_id)}}

    async def async_set_native_value(self, value: float) -> None:
        """Set new temperature offset value."""
        await self._client.set_temperature_offset(value)
        await self._coordinator.async_request_refresh()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_native_value = self._coordinator.data.temperature_offset
        self.async_write_ha_state()

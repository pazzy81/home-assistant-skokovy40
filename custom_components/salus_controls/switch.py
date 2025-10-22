"""Hot water pump entity for the Salus Controls device."""

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.core import callback

from homeassistant.const import (
    CONF_DEVICE_ID
)

from .const import (
    DOMAIN,
)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Salus switches from a config entry."""

    coordinator = config_entry.runtime_data
    device_id = config_entry.data[CONF_DEVICE_ID]

    async_add_entities([
        HotWaterEntity("Hot Water Valve", coordinator, coordinator.get_client, device_id)])


class HotWaterEntity(CoordinatorEntity, SwitchEntity):
    """Representation of a hot water."""
    _attr_has_entity_name = True
    _attr_icon = "mdi:water-thermometer"

    def __init__(self, name, coordinator, client, device_id):
        """Initialize the switch."""
        super().__init__(coordinator)
        self._name = name
        self._device_id = device_id
        self._coordinator = coordinator
        self._client = client
        self._is_on = None

    @property
    def name(self):
        """Name of the entity."""
        return self._name

    @property
    def device_info(self):
        """Return information to link this entity with the correct device."""
        return {"identifiers": {(DOMAIN, self._device_id)}}

    @property
    def unique_id(self) -> str:
        """Return the unique ID for this switch."""
        return "_".join([self._device_id, "hot_water_valve"])

    @property
    def is_on(self):
        """If the switch is currently on or off."""
        return self._is_on

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        await self._client.set_hot_water_mode(True)
        await self._coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        await self._client.set_hot_water_mode(False)
        await self._coordinator.async_request_refresh()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._is_on = self._coordinator.data.hot_water_enabled
        self.async_write_ha_state()

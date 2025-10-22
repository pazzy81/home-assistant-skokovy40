"""Thermostat entity for the Salus Controls device."""

from homeassistant.components.climate.const import (
    HVACAction,
    HVACMode,
    ClimateEntityFeature,
    PRESET_NONE,
)

from homeassistant.const import (
    ATTR_TEMPERATURE,
    UnitOfTemperature,
)

from homeassistant.const import (
    CONF_DEVICE_ID
)

from custom_components.salus_controls.state import State

from .const import (
    DOMAIN,
    MAX_TEMP,
    MIN_TEMP
)


from homeassistant.components.climate import ClimateEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.core import callback

PARALLEL_UPDATES = 1

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Salus switches from a config entry."""

    coordinator = config_entry.runtime_data
    device_id = config_entry.data[CONF_DEVICE_ID]

    async_add_entities([ThermostatEntity("Salus Thermostat", coordinator, coordinator.get_client, device_id)])

class ThermostatEntity(CoordinatorEntity, ClimateEntity):
    """Representation of a Salus Thermostat cappabilities."""

    def __init__(self, name, coordinator, client, device_id):
        """Initialize the thermostat."""
        super().__init__(coordinator)
        self._name = name
        self._device_id = device_id
        self._coordinator = coordinator
        self._client = client
        self._state = State()

    @property
    def supported_features(self) -> ClimateEntityFeature:
        """Return the list of supported features."""
        return ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.TURN_OFF | ClimateEntityFeature.TURN_ON

    @property
    def device_info(self):
        """Return information to link this entity with the correct device."""
        return {"identifiers": {(DOMAIN, self._device_id)}}

    @property
    def name(self) -> str:
        """Return the name of the thermostat."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return the unique ID for this thermostat."""
        return "_".join([self._device_id, "climate"])

    @property
    def should_poll(self) -> bool:
        """Return if polling is required."""
        return True

    @property
    def min_temp(self) -> float:
        """Return the minimum temperature."""
        return MIN_TEMP

    @property
    def max_temp(self) -> float:
        """Return the maximum temperature."""
        return MAX_TEMP

    @property
    def temperature_unit(self) -> UnitOfTemperature:
        """Return the unit of measurement."""
        return UnitOfTemperature.CELSIUS

    @property
    def current_temperature(self) -> float:
        """Return the current temperature."""
        return self._state.current_temperature

    @property
    def target_temperature(self) -> float:
        """Return the temperature we try to reach."""
        return self._state.target_temperature

    @property
    def hvac_mode(self) -> HVACMode:
        """Return hvac operation ie. heat, cool mode."""

        return self._state.mode

    @property
    def hvac_modes(self) -> list[HVACMode]:
        """HVAC modes."""
        return [HVACMode.HEAT, HVACMode.OFF]

    @property
    def hvac_action(self) -> HVACAction:
        """Return the current running hvac operation."""
        return self._state.action

    @property
    def preset_mode(self) -> str:
        """Return the current preset mode, e.g., home, away, temp."""
        return PRESET_NONE

    @property
    def preset_modes(self) -> list[str]:
        """Return a list of available preset modes."""
        return [PRESET_NONE]

    async def async_set_temperature(self, **kwargs) -> None:
        """Set new target temperature."""

        temperature = kwargs.get(ATTR_TEMPERATURE)

        if temperature is None:
            return

        await self._client.set_temperature(temperature)
        await self._coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set HVAC mode, via URL commands."""

        await self._client.set_hvac_mode(hvac_mode)
        await self._coordinator.async_request_refresh()

    async def async_turn_off(self) -> None:
        await self.async_set_hvac_mode(HVACMode.OFF)

    async def async_turn_on(self) -> None:
        await self.async_set_hvac_mode(HVACMode.HEAT)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._state = self._coordinator.data
        self.async_write_ha_state()

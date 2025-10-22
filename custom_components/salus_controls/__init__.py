"""Support for Salus Controls iT 500 device."""


import logging

from homeassistant.const import (
    Platform,
    CONF_PASSWORD,
    CONF_USERNAME,
    CONF_DEVICE_ID
)
from homeassistant.helpers import device_registry

from .web_client import WebClient
from .api_client import ApiClient
from .const import DOMAIN
from .coordinator import SalusCoordinator

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [
    Platform.CLIMATE,
    Platform.SWITCH,
    Platform.NUMBER,
    Platform.SELECT
]

async def async_setup_entry(hass, entry) -> bool:
    """Set up components from a config entry."""
    hass.data[DOMAIN] = {}
    if entry.data[CONF_USERNAME]:
        client = create_client_from(entry.data)
        name = entry.data[CONF_DEVICE_ID]

        # assuming API object stored here by __init__.py
        coordinator = SalusCoordinator(hass, client)
        # Fetch initial data so we have data when entities subscribe
        #
        # If the refresh fails, async_config_entry_first_refresh will
        # raise ConfigEntryNotReady and setup will try again later
        #
        # If you do not want to retry setup on failure, use
        # coordinator.async_refresh() instead
        #
        await coordinator.async_config_entry_first_refresh()

        entry.runtime_data = coordinator

        registry = device_registry.async_get(hass)
        registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, name)},
            manufacturer="Salus Controls",
            name="Salus",
            model="iT500",
        )

        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

def create_client_from(config) -> WebClient:
    """Creates a client object based on the specified configuration"""

    username = config[CONF_USERNAME]
    password = config[CONF_PASSWORD]
    device_id = config[CONF_DEVICE_ID]
    use_api_client = True

    _LOGGER.info("Creating Salus client %s", config)

    return ApiClient(username, password, device_id) if use_api_client else WebClient(username, password, device_id)
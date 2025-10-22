"""Config flow to configure Salus iT500 component."""
import logging

import voluptuous as vol


from homeassistant.const import (
    CONF_PASSWORD,
    CONF_USERNAME,
    CONF_DEVICE_ID
)
from homeassistant import config_entries

from .const import DOMAIN

GATEWAY_SETTINGS = {
    vol.Required(CONF_USERNAME): str,
    vol.Required(CONF_PASSWORD): str,
    vol.Required(CONF_DEVICE_ID): str,
}

class SalusFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a Salus config flow."""

    VERSION = 1
    MINOR_VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user to configure a gateway."""
        errors = {}
        if user_input is not None:
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]
            device_id = user_input[CONF_DEVICE_ID]

            # TODO: Try to connect to a Salus Gateway.
            await self.async_set_unique_id(device_id)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                    title="Salus Controls",
                    data={
                        CONF_USERNAME: username,
                        CONF_PASSWORD: password,
                        CONF_DEVICE_ID: device_id,
                    },
                )

        schema = vol.Schema(GATEWAY_SETTINGS)

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

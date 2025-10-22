"""
Adds support for the Salus Thermostat units.
"""
import time
import logging
import xml.etree.ElementTree as ET
import json
import aiohttp
import hashlib

from homeassistant.components.climate.const import (
    HVACMode,
    HVACAction,
)

from homeassistant.helpers.update_coordinator import (
    UpdateFailed,
)

from .state import State

MAX_TOKEN_AGE_SECONDS = 60 * 60

URL_LOGIN = "https://sal-emea-p01-api.arrayent.com/acc/applications/SalusService/sessions"
URL_GET_DATA = "https://sal-emea-p01-api.arrayent.com/zdk/services/zamapi/getDeviceAttributesWithValues"
URL_SET_DATA = "https://sal-emea-p01-api.arrayent.com/zdk/services/zamapi/setMultiDeviceAttributes2"

AUTHORIZATION_TOKEN = "687886-679716122"

TEMPERATURE_SPAN_ATTR = "S15"
TEMPERATURE_OFFSET_ATTR = "S17"
HOT_WATER_STATUS_ATTR = "C45"
HOT_WATER_MODE_ATTR = "C42"
FROST_TEMPERATURE_ATTR = "S09"
CURRENT_TEMPERATURE_ATTR = "A84"
TARGET_TEMPERATURE_ATTR = "A85"
CURRENT_STATE_ATTR = "A87"
AUTO_VS_TEMP_HOLD_MODE_ATTR = "A88"
OFF_MODE_ATTR = "A89"

_LOGGER = logging.getLogger(__name__)

TEMPERATURE_OFFSET_VALUES = [
    -3.0, -2.5, -2.0, -1.5, -1.0, -0.5, 0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]


class DeviceAttributesResponse:
    def __init__(self, content: str):
        self._root = ET.fromstring(content)

    def get_value(self, attributeName: str) -> str:
        return self._root.find(f"./attrList/[name='{attributeName}']/value").text


class ApiClient:
    """Adapter around Salus IT500 mobile application."""

    def __init__(self, username: str, password: str, device_id: str):
        """Initialize the client."""
        self._username = username
        self._password_hash = hashlib.md5(password.encode()).hexdigest()
        self._id = device_id
        self._token = None
        self._token_retrieved_at = None

    async def set_temperature(self, temperature: float) -> None:
        """Set new target temperature, via URL commands."""

        _LOGGER.info("Setting the temperature to %.1f...", temperature)

        options = {"name1": AUTO_VS_TEMP_HOLD_MODE_ATTR, "value1": "1",
                   "name2": TARGET_TEMPERATURE_ATTR, "value2": int(temperature * 100)}
        return_code = await self.set_data(options)

        if return_code == 0:
            _LOGGER.info("Sucessfully set temperature to %.1f", temperature)
        else:
            raise UpdateFailed("Server returned unknown error")

    async def set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set HVAC mode, via URL commands."""

        _LOGGER.info("Setting the HVAC mode to %s...", hvac_mode)

        options = {}
        if hvac_mode == HVACMode.OFF:
            options = {"name1": OFF_MODE_ATTR, "value1": "1"}
        elif hvac_mode == HVACMode.HEAT:
            options = {"name1": OFF_MODE_ATTR, "value1": "0"}

        return_code = await self.set_data(options)

        if return_code == 0:
            _LOGGER.info("Sucessfully set the HVAC mode to %s", hvac_mode)
        else:
            raise UpdateFailed("Could not set the HVAC mode")

    async def set_hot_water_mode(self, enabled: bool) -> None:
        """Set HVAC mode, via URL commands."""

        _LOGGER.info("Setting the hot water mode to %s...", str(enabled))

        mode = "2" if enabled else "3"

        options = {"name1": HOT_WATER_MODE_ATTR, "value1": mode}
        return_code = await self.set_data(options)

        if return_code == 0:
            _LOGGER.info(
                "Sucessfully set the hot water mode to %s", str(enabled))
        else:
            raise UpdateFailed("Could not set the hot water mode")

    async def set_freeze_protection_temperature(self, temperature: float) -> None:
        """Set freeze protection temperature."""

        _LOGGER.info(
            "Setting the freeze protection temperature to %.1f...", temperature)

        options = {"name1": FROST_TEMPERATURE_ATTR,
                   "value1": int(temperature * 100)}

        return_code = await self.set_data(options)

        if return_code == 0:
            _LOGGER.info(
                "Sucessfully set the freeze protection temperature to %.1f", temperature)
        else:
            raise UpdateFailed(
                "Could not set the freeze protection temperature")

    async def set_temperature_offset(self, temperature: float) -> None:
        """Set temperature offset."""

        _LOGGER.info(
            "Setting the temperature offset to %.1f...", temperature)

        options = {"name1": TEMPERATURE_OFFSET_ATTR,
                   "value1": TEMPERATURE_OFFSET_VALUES.index(temperature)}

        return_code = await self.set_data(options)

        if return_code == 0:
            _LOGGER.info(
                "Sucessfully set the temperature offset to %.1f", temperature)
        else:
            raise UpdateFailed(
                "Could not set the temperature offset")

    async def set_temperature_span(self, value: int) -> None:
        """Set temperature span."""

        _LOGGER.info(
            "Setting the temperature span to index %s...", str(value))

        options = {"name1": TEMPERATURE_SPAN_ATTR,
                   "value1": value}

        return_code = await self.set_data(options)

        if return_code == 0:
            _LOGGER.info(
                "Sucessfully set the temperature span to index %s", str(value))
        else:
            raise UpdateFailed(
                "Could not set the temperature span")

    async def obtain_token(self, session: aiohttp.ClientSession) -> str:
        """Gets the existing session token of the thermostat or retrieves a new one if expired."""

        if self._token is None:
            _LOGGER.info("Retrieving token for the first time this session...")
            await self.get_token(session)
            return self._token

        if self._token_retrieved_at > time.time() - MAX_TOKEN_AGE_SECONDS:
            _LOGGER.debug("Using cached token...")
            return self._token

        _LOGGER.info("Token has expired, getting new one...")
        await self.get_token(session)
        return self._token

    async def get_token(self, session: aiohttp.ClientSession) -> None:
        """Get the Session Token of the Thermostat."""

        _LOGGER.info("Getting token from Salus Gateway...")

        payload = {
            "username": self._username,
            "password": self._password_hash}

        headers = {"Authorization": AUTHORIZATION_TOKEN,
                   "Accept": "application/json"}

        try:
            response = await session.post(URL_LOGIN, json=payload, headers=headers)
            body = await response.text()
            data = json.loads(body)

            _LOGGER.info("Sucessfully retrieved token")

            self._token = data["securityToken"]
            self._token_retrieved_at = time.time()
        except Exception as err:
            self._token = None
            self._token_retrieved_at = None
            _LOGGER.error("Error getting the session token: %s", str(err))

    async def get_state(self) -> dict:
        """Retrieves the raw state from the Salus gateway"""

        _LOGGER.debug("Retrieving the device state...")

        async with aiohttp.ClientSession() as session:
            token = await self.obtain_token(session)

            params = {"devId": self._id,
                      "deviceTypeId": "1", "secToken": token}
            try:
                r = await session.get(url=URL_GET_DATA, params=params)
                if not r:
                    _LOGGER.error("Could not get the data")
                    return None
            except BaseException as err:
                _LOGGER.error(
                    "Error Getting the data from Salus")
                raise UpdateFailed(
                    f"Error during communication with the API: {err}")

            body = await r.text()
            _LOGGER.debug("Sucessfully retrieved the device state: %s", body)

            return ApiClient.convert_to_state(DeviceAttributesResponse(body))

    async def set_data(self, options: dict) -> int:
        """Send POST request with token"""

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        async with aiohttp.ClientSession() as session:
            token = await self.obtain_token(session)

            payload = {
                **options,
                "secToken": token,
                "devId": self._id}

            try:
                response = await session.put(URL_SET_DATA, data=payload, headers=headers)
                if not response:
                    _LOGGER.error("Could not get data from Salus.")
                    return None
            except BaseException as err:
                _LOGGER.error(
                    "Error during communication with Salus.")
                raise UpdateFailed(
                    f"Error during communication with the API: {err}")

            body = await response.text()
            _LOGGER.debug(
                "Sucessfully retrieved response from action: %s", body)
            xml = ET.fromstring(body)
            error_message = xml.find("./errorMsg")
            return_code = xml.find("./retCode")

            if error_message is not None:
                raise UpdateFailed(
                    f"Error during communication with the API: {error_message.text}")
            elif return_code is None:
                raise UpdateFailed(
                    f"Response does not contain return code")
            else:
                return int(return_code.text)

    @classmethod
    def convert_to_state(cls, response: DeviceAttributesResponse) -> State:
        """Converts the data payload to a state object"""
        state = State()
        state.target_temperature = float(
            response.get_value(TARGET_TEMPERATURE_ATTR)) * 0.01
        state.current_temperature = float(
            response.get_value(CURRENT_TEMPERATURE_ATTR)) * 0.01
        state.frost = float(response.get_value(FROST_TEMPERATURE_ATTR)) * 0.01
        state.action = HVACAction.HEATING if response.get_value(
            CURRENT_STATE_ATTR) == "1" else HVACAction.IDLE
        state.mode = HVACMode.OFF if response.get_value(
            OFF_MODE_ATTR) == "1" else HVACMode.HEAT
        state.hot_water_enabled = False if response.get_value(
            HOT_WATER_STATUS_ATTR) == "0" else True
        state.temperature_span = int(
            response.get_value(TEMPERATURE_SPAN_ATTR))
        state.temperature_offset = TEMPERATURE_OFFSET_VALUES[
            int(response.get_value(TEMPERATURE_OFFSET_ATTR))]

        return state

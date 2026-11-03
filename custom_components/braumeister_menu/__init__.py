"""Server-side adapter for the local Braumeister Bridge menu API."""

import asyncio

import voluptuous as vol
from aiohttp import ClientError, ClientTimeout
from homeassistant.core import SupportsResponse
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

DOMAIN = "braumeister_menu"
BASE_URL = "http://127.0.0.1:8642/api/"
SCREENS = {
    "open_settings": "101",
    "close_settings": "8101",
    "open_manual": "101",
    "close_manual": "4006",
    "open_recipe_list": "101",
    "close_recipe_list": "6010",
    "open_recipe_selection": "101",
    "cancel_recipe_selection": "2015",
    "recipe_down": "2015",
    "recipe_up": "2015",
}
CONFIG_SCHEMA = vol.Schema(
    {vol.Required(DOMAIN): {vol.Required("device_id"): cv.string}},
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass, config):
    """Register a response-only HA action for one configured device."""
    device_id = config[DOMAIN]["device_id"]
    session = async_get_clientsession(hass)
    lock = asyncio.Lock()

    async def request(method, path, **kwargs):
        async with session.request(
            method, BASE_URL + path, timeout=ClientTimeout(total=2),
            allow_redirects=False, **kwargs,
        ) as response:
            if response.status not in (200, 202):
                raise HomeAssistantError(f"Bridge rejected the request (HTTP {response.status})")
            return await response.json()

    async def navigate(call):
        user = await hass.auth.async_get_user(call.context.user_id) if call.context.user_id else None
        if user is None or not user.is_admin:
            raise HomeAssistantError("An administrator must initiate menu navigation")
        action = call.data["action"]
        if lock.locked():
            raise HomeAssistantError("A menu action is already pending")
        async with lock:
            try:
                status = await request("GET", "status")
                for device in status["devices"]:
                    if device["device_id"].lower() == device_id.lower():
                        break
                else:
                    raise HomeAssistantError("Configured Braumeister is not visible to the bridge")
                parts = device.get("bm_stat", "").split(";", 4)
                fields = parts[3].split("X", 15) if len(parts) >= 4 else []
                age = status["now"] - device.get("bm_stat_received", 0)
                if (
                    len(fields) < 15 or fields[3] != SCREENS[action]
                    or fields[14] != "ph" or not 0 <= age < 5
                ):
                    raise HomeAssistantError("Wait for a fresh matching screen with both actuators off")

                actual_id = device["device_id"]
                queued = await request("POST", "control", json={"device_id": actual_id, "action": action})
                if queued.get("result") != "queued":
                    return {"result": "unconfirmed"}
                deadline = asyncio.get_running_loop().time() + 12
                while asyncio.get_running_loop().time() < deadline:
                    await asyncio.sleep(0.4)
                    outcome = await request("GET", "control")
                    if (outcome.get("device_id"), outcome.get("action")) != (actual_id, action):
                        break
                    if outcome.get("result") in ("confirmed", "expired", "unconfirmed", "state_changed"):
                        result = {"result": outcome["result"]}
                        if result["result"] == "confirmed" and action in (
                            "open_recipe_selection", "recipe_down", "recipe_up",
                        ):
                            snapshot = await request("GET", "status")
                            for entry in snapshot["devices"]:
                                if entry["device_id"] == actual_id:
                                    result["picker"] = recipe_picker(entry)
                                    break
                        return result
                return {"result": "unconfirmed"}
            except (ClientError, TimeoutError, ValueError, KeyError, TypeError) as err:
                raise HomeAssistantError("Could not verify the bridge action") from err

    hass.services.async_register(
        DOMAIN, "navigate", navigate,
        schema=vol.Schema({vol.Required("action"): vol.In(SCREENS)}),
        supports_response=SupportsResponse.ONLY,
    )
    return True


def recipe_picker(device):
    """Return only recipe names and the highlighted slot to the dashboard."""
    parts = device.get("bm_stat", "").split(";", 4)
    fields = parts[3].split("X", 15) if len(parts) >= 4 else []
    if len(fields) < 15 or fields[3] != "2015" or fields[9] not in ("0", "1", "2", "3"):
        return None
    recipes = {}
    for line in device.get("rz", "").splitlines()[1:]:
        head, separator, name = line.split(";", 1)[0].partition(".")
        values = head.split("X")
        if separator and len(values) == 20 and values[0] in ("0", "1", "2", "3"):
            recipes[values[0]] = name.strip()
    return {"slot": int(fields[9]), "recipes": recipes}

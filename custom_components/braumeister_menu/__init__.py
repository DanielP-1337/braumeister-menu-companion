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
    "select_recipe": "2015",
    "open_temperature_editor": "4006",
    "temperature_up": "4007",
    "temperature_down": "4007",
    "confirm_temperature": "4007",
    "cancel_temperature": "4007",
}
PROGRAM_RULES = {
    "acknowledge_hop_addition": {"3080": ({"qH"}, "010")},
    "confirm_whirlpool": {"3510": ({"ph"}, "000")},
    "finish_brewing": {"3610": ({"ph"}, "000")},
    "confirm_lid_removed": {"3010": ({"qH"}, "0DT")},
    "acknowledge_rest_end": {"2910": ({"Pi"}, "010")},
    "confirm_malt_pipe_removed": {"2930": ({"pi", "pH"}, "000")},
    "start_boil": {"2960": ({"pi", "pH"}, "000")},
    "acknowledge_mash_temperature": {"2510": ({"Pi"}, "010")},
    "open_malt_confirmation": {"2610": ({"ph"}, "000")},
    "confirm_malt_added": {"2705": ({"ph"}, "000")},
    "confirm_water_filled": {"2030": ({"ph"}, "000")},
    "start_now": {"2120": ({"ph"}, "000")},
    "start_delay_up": {"2030": ({"ph"}, "000"), "2111": ({"ph"}, "000")},
    "start_delay_down": {"2111": ({"ph"}, "000")},
    "confirm_start_delay": {"2111": ({"ph"}, "000")},
    "cancel_water_prompt": {"2030": ({"ph"}, "000"), "2111": ({"ph"}, "000")},
    "cancel_start_delay": {"2120": ({"ph"}, "000")},
    "request_program_pause": {
        "2910": ({"ph", "Ph", "pH", "PH", "pi", "Pi", "qh", "qH", "qi"}, "010"),
        **{code: ({"ph", "Ph", "pH", "PH", "pi", "Pi", "qh", "qH", "qi"}, "000") for code in ("2930", "2960")},
        "2510": ({"Pi", "PH", "Ph", "ph", "pH", "pi"}, "010"),
        **{code: ({"ph", "Ph", "pH", "PH", "pi", "Pi", "qh", "qH", "qi"}, "000")
           for code in ("2610", "2705", "2810", "2820")},
        "2300": ({"ph", "Ph"}, "000"),
        "2310": ({"ph", "Ph"}, "000"),
        "2410": ({"ph", "Ph", "pH", "PH", "pi", "Pi", "qh", "qH", "qi"}, "000"),
    },
    "abort_program": {**{code: ({"ph"}, "120") for code in ("2510", "2610", "2705", "2810", "2820", "2910", "2930", "2960")}, "2310": ({"ph"}, "120"), "2300": ({"ph"}, "120"), "2410": ({"ph"}, "120")},
    "resume_program": {"2300": ({"ph"}, "120"), "2310": ({"ph"}, "120"), "2810": ({"ph"}, "120")},
}
ACTUATOR_FLAGS = {
    "pump_on": {"ph", "pH", "pi"},
    "pump_off": {"Ph", "PH", "Pi"},
    "heater_on": {"ph", "Ph"},
    "heater_off": {"pH", "PH", "Pi", "pi"},
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
                fields = parts[3].split("X") if len(parts) >= 4 else []
                age = status["now"] - device.get("bm_stat_received", 0)
                actuator = action in ACTUATOR_FLAGS
                program = action in PROGRAM_RULES
                screen = fields[3] if program and len(fields) >= 16 else "4006" if actuator else SCREENS.get(action)
                program_rule = PROGRAM_RULES[action].get(screen) if program else None
                flags = program_rule[0] if program_rule else ACTUATOR_FLAGS[action] if actuator else {"ph"}
                if not 0 <= age < 5:
                    raise HomeAssistantError("The bridge has no fresh device status (less than 5 seconds old)")
                if len(fields) < 15 or fields[3] != screen:
                    raise HomeAssistantError("The device is not on the screen required for this action")
                if fields[14] not in flags:
                    raise HomeAssistantError("The current pump and heater state does not allow this action")
                if program and (program_rule is None or len(fields) < 16 or fields[15] != program_rule[1]):
                    raise HomeAssistantError("The current program screen or pause indicator does not allow this action")
                if action == "select_recipe" and (len(fields) < 16 or fields[15] != "000"):
                    raise HomeAssistantError("Recipe selection must not be interrupted")
                if (actuator or program) and device.get("last_response_source") not in ("cloud", "local_control", "local"):
                    raise HomeAssistantError("The bridge has no recent acknowledged device response")

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
                        if result.get("result") == "confirmed":
                            hass.bus.async_fire("braumeister_menu_updated", {"device_id": actual_id})
                        return result
                return {"result": "unconfirmed"}
            except (ClientError, TimeoutError, ValueError, KeyError, TypeError) as err:
                raise HomeAssistantError("Could not verify the bridge action") from err

    async def get_recipe_picker(call):
        """Read the existing Bridge snapshot without queuing a device command."""
        user = await hass.auth.async_get_user(call.context.user_id) if call.context.user_id else None
        if user is None or not user.is_admin:
            raise HomeAssistantError("An administrator must request the recipe picker")
        try:
            snapshot = await request("GET", "status")
            for device in snapshot["devices"]:
                if device["device_id"].lower() == device_id.lower():
                    age = snapshot["now"] - device.get("bm_stat_received", 0)
                    return {"picker": recipe_picker(device) if 0 <= age < 5 else None}
            return {"picker": None}
        except (ClientError, TimeoutError, ValueError, KeyError, TypeError) as err:
            raise HomeAssistantError("Could not read the recipe picker") from err

    hass.services.async_register(
        DOMAIN, "get_recipe_picker", get_recipe_picker,
        schema=vol.Schema({}), supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN, "navigate", navigate,
        schema=vol.Schema({vol.Required("action"): vol.In(SCREENS)}),
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN, "set_actuator", navigate,
        schema=vol.Schema({vol.Required("action"): vol.In(ACTUATOR_FLAGS)}),
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN, "program_control", navigate,
        schema=vol.Schema({vol.Required("action"): vol.In(PROGRAM_RULES)}),
        supports_response=SupportsResponse.ONLY,
    )
    return True


def recipe_picker(device):
    """Return only recipe names and the highlighted slot to the dashboard."""
    parts = device.get("bm_stat", "").split(";", 4)
    fields = parts[3].split("X", 15) if len(parts) >= 4 else []
    if len(fields) < 15 or fields[3] != "2015":
        return None
    recipes = {}
    for line in device.get("rz", "").splitlines():
        head, separator, name = line.split(";", 1)[0].strip().partition(".")
        values = head.split("X")
        if separator and name.strip() and len(values) == 20 and all(v.lstrip("-").isdigit() for v in values):
            slot = int(values[0])
            if slot in range(9):
                recipes[str(slot)] = name.strip()
    if fields[9] not in recipes:
        return None
    return {"slot": int(fields[9]), "recipes": recipes}

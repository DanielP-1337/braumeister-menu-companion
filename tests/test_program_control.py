"""HA adapter contract using real voluptuous schemas and synthetic HTTP replies."""

from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
import voluptuous as vol


DEVICE = "TEST"


def status(screen, flags, indicator, age=0.5, source="cloud"):
    fields = ["0", "12:00", "C", screen, "420", "42", "0", "0", "4", "0", "0", "0", "0", "000", flags, indicator]
    return {"now": 100, "devices": [{"device_id": DEVICE, "bm_stat_received": 100-age,
            "last_response_source": source, "bm_stat": "FW;TEST;1;" + "X".join(fields)}]}


async def adapter(snapshot, admin=True):
    calls, handlers = [], {}
    events = []
    queued_action = [None]

    class HAError(Exception):
        pass

    class Response:
        status = 200

        def __init__(self, result):
            self.result = result

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def json(self):
            return self.result

    class Session:
        def request(self, method, url, **kwargs):
            calls.append((method, url, kwargs))
            if method == "POST":
                queued_action[0] = kwargs["json"]["action"]
                return Response({"result": "queued"})
            if url.endswith("status"):
                return Response(snapshot)
            return Response({"device_id": DEVICE, "action": queued_action[0], "result": "confirmed"})

    def mod(**values):
        result = ModuleType("stub")
        result.__dict__.update(values)
        return result

    stubs = {
        "homeassistant.core": mod(SupportsResponse=SimpleNamespace(ONLY="only")),
        "homeassistant.exceptions": mod(HomeAssistantError=HAError),
        "homeassistant.helpers": mod(config_validation=SimpleNamespace(string=str)),
        "homeassistant.helpers.aiohttp_client": mod(async_get_clientsession=lambda hass: Session()),
    }
    namespace = {"__name__": "companion_under_test"}
    source = Path(__file__).parents[1] / "custom_components/braumeister_menu/__init__.py"
    with patch.dict("sys.modules", stubs):
        exec(compile(source.read_text(encoding="utf-8"), str(source), "exec"), namespace)
    hass = SimpleNamespace(
        bus=SimpleNamespace(async_fire=lambda *args: events.append(args)),
        auth=SimpleNamespace(async_get_user=AsyncMock(return_value=SimpleNamespace(is_admin=admin))),
        services=SimpleNamespace(async_register=lambda domain, name, fn, **kw: handlers.update({name: (fn, kw["schema"])})),
    )
    await namespace["async_setup"](hass, {"braumeister_menu": {"device_id": DEVICE}})

    async def call(service, action=None):
        fn, schema = handlers[service]
        return await fn(SimpleNamespace(data=schema({} if action is None else {"action": action}), context=SimpleNamespace(user_id="user")))

    handlers["_events"] = events
    return call, calls, handlers, HAError


async def test_recipe_snapshot_is_read_only():
    snapshot = status("2015", "ph", "000")
    snapshot["devices"][0]["rz"] = "header\n" + "X".join(["0"] * 20) + ".Recipe A;"
    call, requests, _, _ = await adapter(snapshot)
    assert await call("get_recipe_picker") == {"picker": {"slot": 0, "recipes": {"0": "Recipe A"}}}
    assert len(requests) == 1
    assert requests[0][:2] == ("GET", "http://127.0.0.1:8642/api/status")


async def test_recipe_snapshot_rejects_non_admin_and_stale_status():
    call, requests, _, error = await adapter(status("2015", "ph", "000"), admin=False)
    with pytest.raises(error):
        await call("get_recipe_picker")
    assert requests == []
    call, requests, _, _ = await adapter(status("2015", "ph", "000", age=5))
    assert await call("get_recipe_picker") == {"picker": None}
    assert all(method == "GET" for method, _, _ in requests)


@pytest.mark.parametrize(("service", "action", "screen", "flags", "indicator"), [
    ("program_control", "acknowledge_hop_addition", "3080", "qH", "010"),
    ("program_control", "confirm_whirlpool", "3510", "ph", "000"),
    ("program_control", "finish_brewing", "3610", "ph", "000"),
    ("program_control", "confirm_lid_removed", "3010", "qH", "0DT"),
    ("program_control", "confirm_lid_removed", "3010", "qH", "0D0"),
    ("program_control", "resume_program", "2820", "ph", "120"),
    ("program_control", "acknowledge_rest_end", "2910", "PH", "010"),
    ("program_control", "request_program_pause", "3010", "PH", "000"),
    ("program_control", "resume_program", "3010", "ph", "120"),
    ("program_control", "acknowledge_brew_complete", "3450", "ph", "010"),
    ("program_control", "request_program_pause", "3450", "ph", "010"),
    ("program_control", "resume_program", "3450", "ph", "120"),
    ("program_control", "request_program_pause", "3080", "qH", "010"),
    ("program_control", "resume_program", "3080", "ph", "120"),
    ("program_control", "acknowledge_rest_end", "2910", "Pi", "010"),
    ("program_control", "confirm_malt_pipe_removed", "2930", "pH", "000"),
    ("program_control", "start_boil", "2960", "pi", "000"),
    ("program_control", "request_program_pause", "2910", "Pi", "010"),
    ("program_control", "request_program_pause", "2930", "pH", "000"),
    ("program_control", "request_program_pause", "2960", "pi", "000"),
    ("program_control", "abort_program", "2960", "ph", "120"),
    ("program_control", "acknowledge_mash_temperature", "2510", "Pi", "010"),
    ("program_control", "open_malt_confirmation", "2610", "ph", "000"),
    ("program_control", "confirm_malt_added", "2705", "ph", "000"),
    ("program_control", "request_program_pause", "2810", "PH", "000"),
    ("program_control", "abort_program", "2810", "ph", "120"),
    ("program_control", "confirm_water_filled", "2030", "ph", "000"),
    ("program_control", "cancel_water_prompt", "2030", "ph", "000"),
    ("program_control", "request_program_pause", "2310", "ph", "000"),
    ("program_control", "abort_program", "2310", "ph", "120"),
    ("navigate", "select_recipe", "2015", "ph", "000"),
    ("navigate", "open_temperature_editor", "4006", "ph", "000"),
    ("navigate", "temperature_up", "4007", "ph", "00T"),
    ("navigate", "temperature_down", "4007", "ph", "00T"),
    ("navigate", "confirm_temperature", "4007", "ph", "00T"),
    ("navigate", "cancel_temperature", "4007", "ph", "00T"),
    ("program_control", "start_delay_up", "2030", "ph", "000"),
    ("program_control", "start_delay_down", "2111", "ph", "000"),
    ("program_control", "confirm_start_delay", "2111", "ph", "000"),
    ("program_control", "start_now", "2120", "ph", "000"),
    ("program_control", "cancel_start_delay", "2120", "ph", "000"),
    ("program_control", "cancel_water_prompt", "2111", "ph", "000"),
    ("program_control", "request_program_pause", "2300", "Ph", "000"),
    ("program_control", "request_program_pause", "2410", "PH", "000"),
    ("program_control", "abort_program", "2300", "ph", "120"),
    ("program_control", "abort_program", "2410", "ph", "120"),
    ("program_control", "resume_program", "2300", "ph", "120"),
    ("program_control", "resume_program", "2310", "ph", "120"),
    ("program_control", "resume_program", "2810", "ph", "120"),
])
async def test_supported_adapter_actions(service, action, screen, flags, indicator):
    call, requests, _, _ = await adapter(status(screen, flags, indicator))
    assert (await call(service, action))["result"] == "confirmed"
    posts = [r for r in requests if r[0] == "POST"]
    assert len(posts) == 1
    assert posts[0][2]["json"] == {"device_id": DEVICE, "action": action}
    assert all(url.startswith("http://127.0.0.1:8642/api/") for _, url, _ in requests)


@pytest.mark.parametrize(("action", "screen", "flags", "indicator", "age", "source", "admin"), [
    ("acknowledge_hop_addition", "3080", "qH", "120", .5, "cloud", True),
    ("acknowledge_hop_addition", "3080", "qH", "000", .5, "cloud", True),
    ("acknowledge_hop_addition", "3080", "PH", "010", .5, "cloud", True),
    ("acknowledge_hop_addition", "3070", "qH", "010", .5, "cloud", True),
    ("confirm_whirlpool", "3450", "ph", "010", .5, "cloud", True),
    ("confirm_whirlpool", "3510", "PH", "000", .5, "cloud", True),
    ("finish_brewing", "3510", "ph", "000", .5, "cloud", True),
    ("finish_brewing", "3610", "ph", "120", .5, "cloud", True),
    ("finish_brewing", "3610", "ph", "000", 5, "cloud", True),
    ("confirm_whirlpool", "3510", "ph", "000", .5, "cloud", False),
    ("resume_program", "2410", "ph", "120", .5, "cloud", True),
    ("start_now", "2030", "ph", "000", .5, "cloud", True),
    ("start_now", "2120", "Ph", "000", .5, "cloud", True),
    ("start_now", "2120", "ph", "000", 5, "cloud", True),
    ("start_now", "2120", "ph", "000", .5, "cloud", False),
    ("resume_program", "2300", "ph", "000", .5, "cloud", True),
    ("abort_program", "2410", "ph", "000", .5, "cloud", True),
    ("abort_program", "2410", "PH", "120", .5, "cloud", True),
    ("request_program_pause", "2410", "PH", "120", .5, "cloud", True),
    ("request_program_pause", "2310", "ph", "120", .5, "cloud", True),
    ("resume_program", "2300", "ph", "120", 5, "cloud", True),
    ("resume_program", "2300", "ph", "120", -1, "cloud", True),
    ("resume_program", "2300", "ph", "120", .5, "unknown", True),
    ("resume_program", "2300", "ph", "120", .5, "cloud", False),
])
async def test_refused_context_never_posts(action, screen, flags, indicator, age, source, admin):
    call, requests, _, error = await adapter(status(screen, flags, indicator, age, source), admin)
    with pytest.raises(error):
        await call("program_control", action)
    assert not any(r[0] == "POST" for r in requests)


async def test_rejection_identifies_actual_context_before_actuator_check():
    call, requests, _, error = await adapter(status("3070", "qH", "000"))
    with pytest.raises(error, match="program screen or pause indicator") as caught:
        await call("program_control", "acknowledge_hop_addition")
    assert "action=acknowledge_hop_addition, screen=3070, actuators=qH, indicator=000" in str(caught.value)
    assert not any(r[0] == "POST" for r in requests)


async def test_actuator_rejection_identifies_actual_context():
    call, requests, _, error = await adapter(status("3080", "PH", "010"))
    with pytest.raises(error, match="pump and heater") as caught:
        await call("program_control", "acknowledge_hop_addition")
    assert "screen=3080, actuators=PH, indicator=010" in str(caught.value)
    assert not any(r[0] == "POST" for r in requests)


async def test_unverified_actions_are_absent_from_real_service_schemas():
    call, requests, _, _ = await adapter(status("2030", "ph", "000"))
    for action in ("confirm_unknown_step", "select_during_countdown", "$k=4"):
        with pytest.raises(vol.Invalid):
            await call("program_control", action)
    assert requests == []


@pytest.mark.parametrize("source", ["local", "local_control"])
async def test_local_ack_allows_verified_controls_and_requests_refresh(source):
    call, requests, handlers, _ = await adapter(status("2300", "ph", "120", source=source))
    assert (await call("program_control", "resume_program"))["result"] == "confirmed"
    assert handlers["_events"] == [("braumeister_menu_updated", {"device_id": DEVICE})]
    assert all(url.startswith("http://127.0.0.1:8642/api/") for _, url, _ in requests)


async def test_local_stale_status_still_blocks_control():
    call, requests, _, error = await adapter(status("2300", "ph", "120", age=5, source="local"))
    with pytest.raises(error):
        await call("program_control", "resume_program")
    assert not any(method == "POST" for method, _, _ in requests)

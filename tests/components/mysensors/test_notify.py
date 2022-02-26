"""Provide tests for mysensors notify platform."""
from __future__ import annotations

from collections.abc import Callable
from unittest.mock import MagicMock, call

from mysensors.sensor import Sensor

from homeassistant.components.notify import DOMAIN as NOTIFY_DOMAIN
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry


async def test_text_type(
    hass: HomeAssistant,
    text_node: Sensor,
    transport_write: MagicMock,
    integration: tuple[MockConfigEntry, Callable[[str], None]],
) -> None:
    """Test a text type child."""
    await hass.services.async_call(
        NOTIFY_DOMAIN, "mysensors", {"message": "Hello World"}, blocking=True
    )

    assert transport_write.call_count == 1
    assert transport_write.call_args == call("1;1;1;0;47;Hello World\n")

    await hass.services.async_call(
        NOTIFY_DOMAIN,
        "mysensors",
        {"message": "Hello", "target": "Text Node 1 1"},
        blocking=True,
    )

    assert transport_write.call_count == 2
    assert transport_write.call_args == call("1;1;1;0;47;Hello\n")

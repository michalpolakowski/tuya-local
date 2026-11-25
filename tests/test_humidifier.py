"""Tests for the humidifier entity."""

from unittest.mock import MagicMock, Mock

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.tuya_local.const import (
    CONF_DEVICE_ID,
    CONF_PROTOCOL_VERSION,
    CONF_TYPE,
    DOMAIN,
)
from custom_components.tuya_local.helpers.device_config import (
    available_configs,
    get_config,
)
from custom_components.tuya_local.humidifier import (
    TuyaLocalHumidifier,
    async_setup_entry,
)

from .helpers import mock_device


@pytest.mark.asyncio
async def test_init_entry(hass):
    """Test the initialisation."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_TYPE: "dehumidifier",
            CONF_DEVICE_ID: "dummy",
            CONF_PROTOCOL_VERSION: "auto",
        },
    )
    # although async, the async_add_entities function passed to
    # async_setup_entry is called truly asynchronously. If we use
    # AsyncMock, it expects us to await the result.
    m_add_entities = Mock()
    m_device = MagicMock()
    m_device.get_property = Mock(return_value=None)

    hass.data[DOMAIN] = {}
    hass.data[DOMAIN]["dummy"] = {}
    hass.data[DOMAIN]["dummy"]["device"] = m_device

    await async_setup_entry(hass, entry, m_add_entities)
    assert (
        type(hass.data[DOMAIN]["dummy"]["humidifier_dehumidifier"])
        is TuyaLocalHumidifier
    )
    m_add_entities.assert_called_once()


@pytest.mark.asyncio
async def test_init_entry_fails_if_device_has_no_humidifier(hass):
    """Test initialisation when device has no matching entity"""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_TYPE: "kogan_heater",
            CONF_DEVICE_ID: "dummy",
            CONF_PROTOCOL_VERSION: "auto",
        },
    )
    # although async, the async_add_entities function passed to
    # async_setup_entry is called truly asynchronously. If we use
    # AsyncMock, it expects us to await the result.
    m_add_entities = Mock()
    m_device = MagicMock()

    hass.data[DOMAIN] = {}
    hass.data[DOMAIN]["dummy"] = {}
    hass.data[DOMAIN]["dummy"]["device"] = m_device
    try:
        await async_setup_entry(hass, entry, m_add_entities)
        assert False
    except ValueError:
        pass
    m_add_entities.assert_not_called()


@pytest.mark.asyncio
async def test_init_entry_fails_if_config_is_missing(hass):
    """Test initialisation when device has no matching entity"""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_TYPE: "non_existing",
            CONF_DEVICE_ID: "dummy",
            CONF_PROTOCOL_VERSION: "auto",
        },
    )
    # although async, the async_add_entities function passed to
    # async_setup_entry is called truly asynchronously. If we use
    # AsyncMock, it expects us to await the result.
    m_add_entities = Mock()
    m_device = MagicMock()

    hass.data[DOMAIN] = {}
    hass.data[DOMAIN]["dummy"] = {}
    hass.data[DOMAIN]["dummy"]["device"] = m_device
    try:
        await async_setup_entry(hass, entry, m_add_entities)
        assert False
    except ValueError:
        pass
    m_add_entities.assert_not_called()


def _humidifier_configs():
    """Device configs that define a humidifier entity."""
    for cfg_file in sorted(available_configs()):
        cfg = get_config(cfg_file.removesuffix(".yaml"))
        for entity in cfg.all_entities():
            if entity.entity == "humidifier":
                yield pytest.param(entity, id=f"{cfg_file}:{entity.config_id}")


@pytest.mark.parametrize("entity_cfg", _humidifier_configs())
def test_humidifier_entity_can_be_created(entity_cfg, mocker):
    """Every humidifier config should produce a usable entity."""
    device = mock_device({}, mocker)
    humidifier = TuyaLocalHumidifier(device, entity_cfg)
    assert humidifier.min_humidity <= humidifier.max_humidity
    if humidifier._humidity_dp is not None:
        assert humidifier.target_humidity_step > 0


def test_discrete_humidity_step_from_mapping(mocker):
    """Discrete humidity without a range takes min, max and step from the mapping."""
    cfg = get_config("klarta_humea_grande_humidifier")
    entity_cfg = next(e for e in cfg.all_entities() if e.entity == "humidifier")
    humidifier = TuyaLocalHumidifier(mock_device({}, mocker), entity_cfg)
    assert humidifier.min_humidity == 40
    assert humidifier.max_humidity == 80
    assert humidifier.target_humidity_step == 5

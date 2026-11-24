"""Control a Fluval Flex 2.0 light through a Home Assistant infrared emitter."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_entity_registry_updated_event

from .const import CONF_EMITTER

PLATFORMS = [Platform.BUTTON]


type FluvalConfigEntry = ConfigEntry[str]


async def async_setup_entry(hass: HomeAssistant, entry: FluvalConfigEntry) -> None:
    """Set up the selected emitter and the buttons captured for this remote."""
    emitter = er.async_resolve_entity_id(er.async_get(hass), entry.data[CONF_EMITTER])
    if emitter is None:
        raise ConfigEntryError(
            "The IR emitter was removed. Select a replacement in Reconfigure."
        )
    entry.runtime_data = emitter

    @callback
    def emitter_updated(event: Event) -> None:
        if event.data.get("old_entity_id") == emitter:
            hass.config_entries.async_schedule_reload(entry.entry_id)

    entry.async_on_unload(
        async_track_entity_registry_updated_event(hass, emitter, emitter_updated)
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)


async def async_unload_entry(hass: HomeAssistant, entry: FluvalConfigEntry) -> None:
    """Remove the buttons and release their emitter subscriptions."""
    await hass.config_entries.async_unload_platforms_or_raise(entry, PLATFORMS)

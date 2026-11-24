"""One-shot Fluval remote keys through Home Assistant's infrared platform."""

from infrared_protocols.commands.nec import NECCommand

from homeassistant.components.button import ButtonEntity
from homeassistant.components.infrared import InfraredEmitterConsumerEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import FluvalConfigEntry
from .codes import ADDRESS, COMMANDS
from .const import DOMAIN

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: FluvalConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add one button per learned command, grouped under the aquarium."""
    async_add_entities(
        FluvalButton(entry, key, command) for key, command in COMMANDS.items()
    )


class FluvalButton(InfraredEmitterConsumerEntity, ButtonEntity):
    """A key on the Fluval remote."""

    _attr_has_entity_name = True

    def __init__(self, entry: FluvalConfigEntry, key: str, command: int) -> None:
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="Fluval",
            model="Flex 2.0",
            name=entry.title,
        )
        self._infrared_emitter_entity_id = entry.runtime_data
        self._command = NECCommand(address=ADDRESS, command=command)

    async def async_press(self) -> None:
        """Press this physical remote key once."""
        await self._send_command(self._command)

"""Run the Fluval integration on Home Assistant with an in-memory IR emitter."""

import json
from pathlib import Path
import sys
import tempfile
import unittest

from homeassistant import bootstrap, loader
from homeassistant.components.infrared import InfraredCommand, InfraredEmitterEntity
from homeassistant.components.infrared.const import DATA_COMPONENT
from homeassistant.config_entries import ConfigEntries, ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component
from infrared_protocols.commands.nec import NECCommand


DOMAIN = "fluval_flex_ir"
TESTS = Path(__file__).resolve().parent
CAPTURES = json.loads((TESTS / "fixtures" / "fluval_flex_2_0.json").read_text())


class RecordingEmitter(InfraredEmitterEntity):
    def __init__(self, name: str) -> None:
        self._attr_name = name
        self._attr_unique_id = name
        self.transmissions: list[InfraredCommand] = []

    async def async_send_command(self, command: InfraredCommand) -> None:
        self.transmissions.append(command)

    def set_online(self, online: bool) -> None:
        self._attr_available = online
        self.async_write_ha_state()


class FluvalIntegrationTest(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # HA imports custom_components as a namespace package across test instances.
        sys.path.insert(0, str(TESTS.parent))
        cls.addClassCleanup(sys.path.remove, str(TESTS.parent))

    async def asyncSetUp(self) -> None:
        config = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.hass = HomeAssistant(str(config))
        self.addAsyncCleanup(self.hass.async_stop, force=True)
        loader.async_setup(self.hass)
        self.hass.config.skip_pip = True
        self.hass.config_entries = ConfigEntries(self.hass, {})
        self.assertTrue(await bootstrap.async_load_base_functionality(self.hass))
        self.assertTrue(await async_setup_component(self.hass, "infrared", {}))
        await self.hass.async_start()

        self.registry = er.async_get(self.hass)
        self.flows = self.hass.config_entries.flow
        self.emitter = RecordingEmitter("Aquarium emitter")
        self.replacement = RecordingEmitter("Replacement emitter")

    async def configure_tank(self) -> ConfigEntry:
        component = self.hass.data[DATA_COMPONENT]
        await component.async_add_entities([self.emitter, self.replacement])
        form = await self.flows.async_init(DOMAIN, context={"source": "user"})
        self.assertEqual(form["type"], "form")
        self.selection = {"name": "Test aquarium", "emitter": self.emitter.entity_id}
        result = await self.flows.async_configure(form["flow_id"], self.selection)
        self.assertEqual(result["type"], "create_entry")
        entry = result["result"]
        await self.hass.async_block_till_done()
        self.assertEqual(entry.state, ConfigEntryState.LOADED)
        return entry

    def buttons_for(self, entry: ConfigEntry) -> dict[str, str]:
        return {
            entity.translation_key: entity.entity_id
            for entity in er.async_entries_for_config_entry(self.registry, entry.entry_id)
            if entity.domain == "button"
        }

    async def press(self, entity_id: str) -> None:
        await self.hass.services.async_call(
            "button", "press", {"entity_id": entity_id}, blocking=True
        )

    async def test_every_key_matches_its_handset_recording(self) -> None:
        entry = await self.configure_tank()
        buttons = self.buttons_for(entry)
        self.assertEqual(len(CAPTURES), 24)
        self.assertEqual(buttons.keys(), CAPTURES.keys())
        learned = set()
        for key, recording in CAPTURES.items():
            with self.subTest(key=key):
                # The receiver appends its 15 ms idle timeout after the final mark.
                self.assertEqual(recording[-1], -15000)
                expected = recording[:-1]
                captured = NECCommand.from_raw_timings(expected)
                self.assertIsNotNone(captured, "Handset recording failed NEC integrity checks")
                learned.add((captured.address, captured.command))

                self.emitter.transmissions.clear()
                await self.press(buttons[key])
                self.assertEqual(len(self.emitter.transmissions), 1)
                outgoing = self.emitter.transmissions[0]
                self.assertEqual(outgoing.modulation, 38000)
                timings = outgoing.get_raw_timings()
                decoded = NECCommand.from_raw_timings(timings)
                self.assertIsNotNone(decoded)
                self.assertEqual(decoded.address, captured.address)
                self.assertEqual(decoded.command, captured.command)
                self.assertEqual(decoded.repeat_count, 0)
                self.assertEqual(len(timings), len(expected))
                for emitted, observed in zip(timings, expected, strict=True):
                    self.assertAlmostEqual(emitted, observed, delta=abs(observed) * 0.15)
        self.assertEqual(len(learned), len(CAPTURES), "Each handset key has a distinct frame")

    async def test_emitter_setup_availability_rename_and_replacement(self) -> None:
        no_emitter = await self.flows.async_init(DOMAIN, context={"source": "user"})
        self.assertEqual(no_emitter["reason"], "no_emitters")
        entry = await self.configure_tank()
        buttons = self.buttons_for(entry)
        duplicate = await self.flows.async_init(DOMAIN, context={"source": "user"})
        result = await self.flows.async_configure(duplicate["flow_id"], self.selection)
        self.assertEqual(result["reason"], "already_configured")

        for online in (False, True):
            self.emitter.set_online(online)
            await self.hass.async_block_till_done()
            for entity_id in buttons.values():
                self.assertEqual(self.hass.states.get(entity_id).state != "unavailable", online)

        self.registry.async_update_entity(self.emitter.entity_id, new_entity_id="infrared.renamed")
        await self.hass.async_block_till_done()
        self.assertEqual(buttons, self.buttons_for(entry))
        await self.press(buttons["red"])
        self.assertEqual(len(self.emitter.transmissions), 1)

        form = await self.flows.async_init(
            DOMAIN, context={"source": "reconfigure", "entry_id": entry.entry_id}
        )
        result = await self.flows.async_configure(
            form["flow_id"], self.selection | {"emitter": self.replacement.entity_id}
        )
        self.assertEqual(result["reason"], "reconfigure_successful")
        await self.hass.async_block_till_done()
        self.assertEqual(buttons, self.buttons_for(entry))
        await self.press(buttons["red"])
        self.assertEqual(len(self.replacement.transmissions), 1)
        self.assertEqual(len(self.emitter.transmissions), 1)
        self.assertTrue(await self.hass.config_entries.async_unload(entry.entry_id))


if __name__ == "__main__":
    unittest.main()

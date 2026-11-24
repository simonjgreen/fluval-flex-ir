"""Set up or move a Fluval aquarium's infrared emitter."""

from typing import Any

import probatio

from homeassistant.components.infrared import DOMAIN as IR_DOMAIN, async_get_emitters
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_NAME
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.selector import EntitySelector, EntitySelectorConfig

from .const import CONF_EMITTER, DEFAULT_NAME, DOMAIN


class FluvalFlexConfigFlow(ConfigFlow, domain=DOMAIN):
    """Configure a named aquarium and the emitter pointing at its lamp."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Add a Fluval aquarium."""
        return self._setup_form("user", user_input)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Change the name or emitter without losing button entity IDs."""
        return self._setup_form(
            "reconfigure", user_input, self._get_reconfigure_entry()
        )

    def _setup_form(
        self,
        step: str,
        user_input: dict[str, Any] | None,
        entry: ConfigEntry | None = None,
    ) -> ConfigFlowResult:
        emitters = async_get_emitters(self.hass)
        if not emitters:
            return self.async_abort(reason="no_emitters")

        registry = er.async_get(self.hass)
        errors: dict[str, str] = {}
        if user_input is not None:
            emitter = user_input[CONF_EMITTER]
            name = user_input[CONF_NAME].strip()
            if not name:
                errors[CONF_NAME] = "empty_name"
            elif emitter not in emitters:
                errors[CONF_EMITTER] = "invalid_emitter"
            else:
                registered = registry.async_get(emitter)
                data = {
                    CONF_NAME: name,
                    CONF_EMITTER: registered.id if registered else emitter,
                }
                self._async_abort_entries_match(data)
                if entry is not None:
                    return self.async_update_reload_and_abort(
                        entry, title=name, data=data
                    )
                return self.async_create_entry(title=name, data=data)

        schema = probatio.Schema(
            {
                probatio.Required(CONF_NAME, default=DEFAULT_NAME): str,
                probatio.Required(CONF_EMITTER): EntitySelector(
                    EntitySelectorConfig(domain=IR_DOMAIN, include_entities=emitters)
                ),
            }
        )
        if entry is not None:
            schema = self.add_suggested_values_to_schema(
                schema,
                {
                    CONF_NAME: entry.title,
                    CONF_EMITTER: er.async_resolve_entity_id(
                        registry, entry.data[CONF_EMITTER]
                    ),
                },
            )
        if user_input:
            schema = self.add_suggested_values_to_schema(schema, user_input)
        return self.async_show_form(step_id=step, data_schema=schema, errors=errors)

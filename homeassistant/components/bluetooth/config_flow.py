"""Config flow to configure the Bluetooth integration."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

import voluptuous as vol

from homeassistant.components import onboarding
from homeassistant.config_entries import ConfigFlow
from homeassistant.helpers.typing import DiscoveryInfoType

from .const import ADAPTER_ADDRESS, CONF_ADAPTER, CONF_DETAILS, DOMAIN, AdapterDetails
from .util import adapter_human_name, adapter_unique_name, async_get_bluetooth_adapters

if TYPE_CHECKING:
    from homeassistant.data_entry_flow import FlowResult


class BluetoothConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for Bluetooth."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._adapter: str | None = None
        self._details: AdapterDetails | None = None
        self._adapters: dict[str, AdapterDetails] = {}

    async def async_step_integration_discovery(
        self, discovery_info: DiscoveryInfoType
    ) -> FlowResult:
        """Handle a flow initialized by discovery."""
        self._adapter = cast(str, discovery_info[CONF_ADAPTER])
        self._details = cast(AdapterDetails, discovery_info[CONF_DETAILS])
        await self.async_set_unique_id(self._details[ADAPTER_ADDRESS])
        self._abort_if_unique_id_configured()
        self.context["title_placeholders"] = {
            "name": adapter_human_name(self._adapter, self._details[ADAPTER_ADDRESS])
        }
        return await self.async_step_single_adapter()

    async def async_step_single_adapter(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Select an adapter."""
        adapter = self._adapter
        details = self._details
        assert adapter is not None
        assert details is not None

        address = details[ADAPTER_ADDRESS]

        if user_input is not None or not onboarding.async_is_onboarded(self.hass):
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=adapter_unique_name(adapter, address), data={}
            )

        return self.async_show_form(
            step_id="single_adapter",
            description_placeholders={"name": adapter_human_name(adapter, address)},
        )

    async def async_step_multiple_adapters(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initialized by the user."""
        if user_input is not None:
            assert self._adapters is not None
            adapter = user_input[CONF_ADAPTER]
            address = self._adapters[adapter][ADAPTER_ADDRESS]
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=adapter_unique_name(adapter, address), data={}
            )

        configured_addresses = self._async_current_ids()
        self._adapters = await async_get_bluetooth_adapters()
        unconfigured_adapters = [
            adapter
            for adapter, details in self._adapters.items()
            if details[ADAPTER_ADDRESS] not in configured_addresses
        ]
        if not unconfigured_adapters:
            return self.async_abort(reason="no_adapters")
        if len(unconfigured_adapters) == 1:
            self._adapter = list(self._adapters)[0]
            self._details = self._adapters[self._adapter]
            return await self.async_step_single_adapter()

        return self.async_show_form(
            step_id="multiple_adapters",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADAPTER): vol.In(
                        {
                            adapter: adapter_human_name(
                                adapter, self._adapters[adapter][ADAPTER_ADDRESS]
                            )
                            for adapter in sorted(unconfigured_adapters)
                        }
                    ),
                }
            ),
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initialized by the user."""
        return await self.async_step_multiple_adapters()

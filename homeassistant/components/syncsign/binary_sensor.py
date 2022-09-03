"""A sensor platform which reports connected status for SyncSign devices."""
import logging

import syncsign

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up syncsign connected binary sensor."""

    def device_setup():
        # add entities for devices (hubs, etc.)
        client = hass.data[DOMAIN][entry.entry_id]
        result = client.devices.list_devices()
        for device in result.body.get("data"):
            async_add_entities(
                [
                    SyncSignConnectedSensor(
                        client,
                        "device",
                        device["thingName"],
                        device["info"]["friendlyName"],
                    )
                ],
                update_before_add=True,
            )

        # add entities for nodes (which connect to devices, displays etc.)
        result = client.nodes.list_nodes()
        for node in result.body.get("data"):
            async_add_entities(
                [SyncSignConnectedSensor(client, "node", node["nodeId"], node["name"])],
                update_before_add=True,
            )

    await hass.async_add_executor_job(device_setup)


class SyncSignConnectedSensor(BinarySensorEntity):
    """Binary sensor representing the connected status of SyncSign devices and nodes."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:wifi"

    def __init__(
        self,
        client: syncsign.client,
        thing_type: str,
        thing_id: str,
        friendly_name: str,
    ) -> None:
        """Initialize the binary sensor."""
        self._attr_name = "%s Connected" % friendly_name
        self._attr_unique_id = thing_id
        self._attr_is_on = False
        self._client = client
        self._type = thing_type

    def update(self) -> None:
        """Update the state."""
        if self._type == "device":
            result = self._client.devices.get_device(self._attr_unique_id)
            self._attr_is_on = result.body.get("data")["network"]["connected"]
        elif self._type == "node":
            result = self._client.nodes.get_node(self._attr_unique_id)
            self._attr_is_on = result.body.get("data")["onlined"]

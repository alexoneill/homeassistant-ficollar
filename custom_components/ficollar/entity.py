"""Base entity for Fi Collar integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN
from .coordinator import FiDataUpdateCoordinator, PetCoordinatorData


class FiEntity(CoordinatorEntity[FiDataUpdateCoordinator]):
    """Defines a base Fi entity."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        coordinator: FiDataUpdateCoordinator,
        pet_id: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.pet_id = pet_id

    @property
    def pet_data(self) -> PetCoordinatorData | None:
        """Return the coordinator data for this pet."""
        return self.coordinator.data.get(self.pet_id)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information for this pet collar."""
        pet = self.pet_data.pet if self.pet_data else None
        pet_name = pet.name if pet else "Fi Pet"
        model = None
        if self.pet_data and self.pet_data.live_state and self.pet_data.live_state.model_name:
            model = self.pet_data.live_state.model_name
        elif pet and pet.device and pet.device.model_name:
            model = pet.device.model_name
        else:
            model = "Smart Collar"

        return DeviceInfo(
            identifiers={(DOMAIN, self.pet_id)},
            name=pet_name,
            manufacturer="Fi",
            model=model,
            configuration_url="https://app.tryfi.com",
        )

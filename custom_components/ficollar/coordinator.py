"""DataUpdateCoordinator for the Fi Collar integration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING, Any

from pyficollar import FiClient
from pyficollar.exceptions import FiAuthError, FiError, FiNetworkError
from pyficollar.models import ActivitySummary, Pet, PetLiveState, RestSummary, Walk

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN, LOGGER

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry


@dataclass
class PetCoordinatorData:
    """Consolidated state data for a single pet."""

    pet: Pet
    live_state: PetLiveState | None = None
    activity: ActivitySummary | None = None
    rest: RestSummary | None = None
    last_walk: Walk | None = None


class FiDataUpdateCoordinator(DataUpdateCoordinator[dict[str, PetCoordinatorData]]):
    """Class to manage fetching TryFi data."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        client: FiClient,
        update_interval_seconds: int = DEFAULT_SCAN_INTERVAL,
    ) -> None:
        """Initialize the coordinator."""
        self.client = client
        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=update_interval_seconds),
        )

    def _fetch_pet_details(self, pet: Pet) -> PetCoordinatorData:
        """Fetch details for a single pet synchronously in the executor."""
        live_state: PetLiveState | None = None
        activity: ActivitySummary | None = None
        rest: RestSummary | None = None
        last_walk: Walk | None = None

        try:
            live_state = self.client.get_pet_live_state(pet.id)
        except Exception as err:  # pylint: disable=broad-except
            LOGGER.debug("Could not fetch live state for pet %s: %s", pet.name, err)

        try:
            activity = self.client.get_pet_activity(pet.id)
        except Exception as err:  # pylint: disable=broad-except
            LOGGER.debug("Could not fetch activity for pet %s: %s", pet.name, err)

        try:
            rest = self.client.get_pet_rest(pet.id)
        except Exception as err:  # pylint: disable=broad-except
            LOGGER.debug("Could not fetch rest data for pet %s: %s", pet.name, err)

        try:
            last_walk = self.client.get_last_walk(pet.id)
        except Exception as err:  # pylint: disable=broad-except
            LOGGER.debug("Could not fetch last walk for pet %s: %s", pet.name, err)

        return PetCoordinatorData(
            pet=pet,
            live_state=live_state,
            activity=activity,
            rest=rest,
            last_walk=last_walk,
        )

    def _sync_update_data(self) -> dict[str, PetCoordinatorData]:
        """Fetch data from the TryFi API synchronously."""
        try:
            pets = self.client.get_pets()
        except FiAuthError as err:
            raise ConfigEntryAuthFailed(
                f"Authentication failed with TryFi API: {err}"
            ) from err
        except (FiNetworkError, FiError) as err:
            raise UpdateFailed(f"Error communicating with TryFi API: {err}") from err

        results: dict[str, PetCoordinatorData] = {}
        for pet in pets:
            results[pet.id] = self._fetch_pet_details(pet)
        return results

    async def _async_update_data(self) -> dict[str, PetCoordinatorData]:
        """Fetch data from the TryFi API asynchronously via executor."""
        return await self.hass.async_add_executor_job(self._sync_update_data)

"""Use case implementation for managing parking spaces (admin)."""

from src.core.domain.exceptions import SpaceNotFoundError
from src.core.domain.models import ParkingSpace
from src.core.ports.outgoing.repositories import ParkingSpaceRepository


class ManageParkingSpacesService:
    """Service that handles parking space management by administrators.

    Allows administrators to add, update, remove, and list parking spaces.
    """

    def __init__(self, space_repo: ParkingSpaceRepository) -> None:
        self._space_repo = space_repo

    def add_space(self, space: ParkingSpace) -> ParkingSpace:
        """Add a new parking space.

        Args:
            space: Parking space to add

        Returns:
            The created parking space
        """
        return self._space_repo.save(space)

    def update_space(self, space: ParkingSpace) -> ParkingSpace:
        """Update an existing parking space.

        Args:
            space: Parking space with updated data

        Returns:
            The updated parking space

        Raises:
            SpaceNotFoundError: If space does not exist
        """
        existing = self._space_repo.find_by_id(space.space_id)
        if existing is None:
            raise SpaceNotFoundError(f"Parking space {space.space_id} not found")
        return self._space_repo.update(space)

    def remove_space(self, space_id: str) -> None:
        """Remove a parking space.

        Args:
            space_id: Space identifier to remove

        Raises:
            SpaceNotFoundError: If space does not exist
        """
        existing = self._space_repo.find_by_id(space_id)
        if existing is None:
            raise SpaceNotFoundError(f"Parking space {space_id} not found")
        self._space_repo.delete(space_id)

    def get_all_spaces(self) -> list[ParkingSpace]:
        """Get all parking spaces.

        Returns:
            List of all parking spaces
        """
        return self._space_repo.find_all()

from typing import Any, Protocol


class ICRUDRepository(Protocol):
    """Generic read access to one registered entity model (a table or a collection)."""

    def get_one_by_id(self, id: str) -> dict[str, Any] | None: ...

    def get_list(
        self, offset: int, limit: int, filters: dict[str, str]
    ) -> tuple[list[dict[str, Any]], int]:
        """Return one page of rows and the total row count matching the filters.

        Raises InvalidFilterError for unknown fields or values of the wrong type.
        """
        ...

    def describe(self) -> dict[str, Any]:
        """Return an Avro-style schema of the fields exposed to clients."""
        ...


class ICRUDRepositoryFactory(Protocol):
    def get(self, entity_model_slug: str) -> ICRUDRepository | None: ...

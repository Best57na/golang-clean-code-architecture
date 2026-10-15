from typing import Any

from bson import ObjectId
from pydantic import BaseModel
from pymongo.collection import Collection

from app.domain.errors import InvalidFilterError
from app.shared.crud.avro_schema import generate_avro_schema
from app.shared.crud.converter import convert_query_value


class MongoCRUDRepository:
    """ICRUDRepository for one MongoDB collection described by a Pydantic schema."""

    def __init__(
        self,
        collection: Collection,
        schema: type[BaseModel],
        name: str,
        hidden_fields: frozenset[str] = frozenset(),
    ):
        self._collection = collection
        self._name = name
        self._hidden_fields = hidden_fields
        self._fields = {
            field_name: field.annotation
            for field_name, field in schema.model_fields.items()
            if field_name not in hidden_fields
        }

    def get_one_by_id(self, id: str) -> dict[str, Any] | None:
        if not ObjectId.is_valid(id):
            return None
        document = self._collection.find_one({"_id": ObjectId(id)})
        return self._to_dict(document) if document else None

    def get_list(
        self, offset: int, limit: int, filters: dict[str, str]
    ) -> tuple[list[dict[str, Any]], int]:
        query = self._build_query(filters)
        cursor = self._collection.find(query).sort("_id", 1).skip(offset).limit(limit)
        documents = [self._to_dict(document) for document in cursor]
        return documents, self._collection.count_documents(query)

    def describe(self) -> dict[str, Any]:
        return generate_avro_schema(self._name, [("id", str), *self._fields.items()])

    def _build_query(self, filters: dict[str, str]) -> dict[str, Any]:
        query = {}
        for name, value in filters.items():
            if name not in self._fields:
                raise InvalidFilterError(f"unknown filter field: {name}")
            try:
                query[name] = convert_query_value(self._fields[name], value)
            except ValueError as exc:
                raise InvalidFilterError(f"invalid value for {name}: {value}") from exc
        return query

    def _to_dict(self, document: dict[str, Any]) -> dict[str, Any]:
        data = {
            key: str(value) if isinstance(value, ObjectId) else value
            for key, value in document.items()
            if key != "_id" and key not in self._hidden_fields
        }
        return {"id": str(document["_id"]), **data}

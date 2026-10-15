from typing import Any

from sqlalchemy import ColumnElement, func, inspect, select
from sqlalchemy.orm import Session, sessionmaker

from app.domain.errors import InvalidFilterError
from app.interface.repositories.postgres.models import Base
from app.shared.crud.avro_schema import generate_avro_schema
from app.shared.crud.converter import convert_name_to_crud_slug, convert_query_value


class PostgresCRUDRepository:
    """ICRUDRepository for one SQLAlchemy model. Hidden fields are never read or filtered."""

    def __init__(
        self,
        session_factory: sessionmaker[Session],
        model: type[Base],
        hidden_fields: frozenset[str] = frozenset(),
    ):
        self._session_factory = session_factory
        self._model = model
        mapper = inspect(model)
        self._columns = {
            attr.key: attr.columns[0]
            for attr in mapper.column_attrs
            if attr.key not in hidden_fields
        }
        self._primary_key = mapper.primary_key[0]

    def get_one_by_id(self, id: str) -> dict[str, Any] | None:
        try:
            key = convert_query_value(self._python_type(self._primary_key), id)
        except ValueError:
            return None
        with self._session_factory() as session:
            row = session.get(self._model, key)
            return self._to_dict(row) if row else None

    def get_list(
        self, offset: int, limit: int, filters: dict[str, str]
    ) -> tuple[list[dict[str, Any]], int]:
        conditions = self._build_conditions(filters)
        with self._session_factory() as session:
            total = session.scalar(select(func.count()).select_from(self._model).where(*conditions))
            rows = session.scalars(
                select(self._model)
                .where(*conditions)
                .order_by(self._primary_key)
                .offset(offset)
                .limit(limit)
            ).unique()
            return [self._to_dict(row) for row in rows], total or 0

    def describe(self) -> dict[str, Any]:
        return generate_avro_schema(
            convert_name_to_crud_slug(self._model.__tablename__),
            [(name, self._python_type(column)) for name, column in self._columns.items()],
        )

    def _build_conditions(self, filters: dict[str, str]) -> list[ColumnElement[bool]]:
        conditions = []
        for name, value in filters.items():
            column = self._columns.get(name)
            if column is None:
                raise InvalidFilterError(f"unknown filter field: {name}")
            try:
                conditions.append(column == convert_query_value(self._python_type(column), value))
            except ValueError as exc:
                raise InvalidFilterError(f"invalid value for {name}: {value}") from exc
        return conditions

    def _to_dict(self, row: Base) -> dict[str, Any]:
        return {name: getattr(row, name) for name in self._columns}

    @staticmethod
    def _python_type(column: Any) -> type:
        try:
            return column.type.python_type
        except NotImplementedError:
            return str

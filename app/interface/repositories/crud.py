from collections.abc import Callable
from dataclasses import dataclass, field

from pydantic import BaseModel
from pymongo.database import Database
from sqlalchemy.orm import Session, sessionmaker

from app.domain.repositories.crud import ICRUDRepository
from app.interface.repositories.mongodb.crud import MongoCRUDRepository
from app.interface.repositories.postgres.crud import PostgresCRUDRepository
from app.interface.repositories.postgres.models import Base
from app.shared.crud.converter import convert_name_to_crud_slug


@dataclass(frozen=True)
class PostgresCRUDModel:
    model: type[Base]
    hidden_fields: frozenset[str] = field(default_factory=frozenset)

    @property
    def slug(self) -> str:
        return convert_name_to_crud_slug(self.model.__tablename__)


@dataclass(frozen=True)
class MongoCRUDModel:
    collection: str
    schema: type[BaseModel]
    hidden_fields: frozenset[str] = field(default_factory=frozenset)

    @property
    def slug(self) -> str:
        return convert_name_to_crud_slug(self.collection)


CRUDModel = PostgresCRUDModel | MongoCRUDModel


class CRUDRepositoryFactory:
    """ICRUDRepositoryFactory: picks the repository matching the model's datasource."""

    def __init__(
        self,
        models: list[CRUDModel],
        session_factory: sessionmaker[Session],
        mongo_database: Callable[[], Database],
    ):
        self._models = {model.slug: model for model in models}
        self._session_factory = session_factory
        # A callable so MongoDB is only connected when a Mongo model is requested
        self._mongo_database = mongo_database

    def get(self, entity_model_slug: str) -> ICRUDRepository | None:
        match self._models.get(entity_model_slug):
            case PostgresCRUDModel() as model:
                return PostgresCRUDRepository(
                    self._session_factory, model.model, model.hidden_fields
                )
            case MongoCRUDModel() as model:
                return MongoCRUDRepository(
                    self._mongo_database()[model.collection],
                    model.schema,
                    model.slug,
                    model.hidden_fields,
                )
            case _:
                return None

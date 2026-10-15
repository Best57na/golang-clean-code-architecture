from enum import StrEnum
from typing import Any

from pydantic import BaseModel


class Datasource(StrEnum):
    POSTGRESQL = "postgresql"
    MONGODB = "mongodb"


class DataResponse(BaseModel):
    data: dict[str, Any]
    data_schema: dict[str, Any]


class DataListResponse(BaseModel):
    data: list[dict[str, Any]]
    page: int
    page_size: int
    total_page: int
    total_data: int
    data_schema: dict[str, Any]

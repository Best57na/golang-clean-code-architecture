from app.interface.repositories.crud import CRUDModel, PostgresCRUDModel
from app.interface.repositories.postgres.models import UserModel, UserPermissionModel

# Entity models exposed through /api/v1/data/{slug}. The slug is the table or
# collection name with "_" replaced by "-".
CRUD_MODELS: list[CRUDModel] = [
    # PostgreSQL
    PostgresCRUDModel(UserModel, hidden_fields=frozenset({"password"})),
    PostgresCRUDModel(UserPermissionModel),
    # user_tokens is intentionally not registered: it would expose other users' tokens.
    # MongoDB, e.g.: MongoCRUDModel("products", ProductDocument)
]

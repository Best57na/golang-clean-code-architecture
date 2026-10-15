# Python Clean Code Architecture (FastAPI)

A Python port of [max38/golang-clean-code-architecture](https://github.com/max38/golang-clean-code-architecture).
It keeps the same layers (domain, usecases, interface, infrastructure), the same routes and
the same error format, built with **FastAPI, SQLAlchemy 2.0, Pydantic v2, PyJWT, bcrypt and PyMongo**.

Features:
- JWT authentication: register, login, refresh token, logout, profile.
- Generic read-only CRUD API over PostgreSQL tables and MongoDB collections.
- 68 automated tests (unit, integration, API).

---

## Quick start

### Option A: Docker Compose (API + PostgreSQL + MongoDB)

```bash
cd python
docker compose up --build
```

Open http://localhost:3000/docs for the interactive Swagger UI.

### Option B: Run locally

```bash
cd python
python -m venv .venv
.venv/Scripts/activate            # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -e ".[dev]"
cp env.template .env              # then set PYAPP_SECRET_KEY

docker compose up -d db mongodb   # or use your own PostgreSQL / MongoDB
python -m app.infrastructure.database.postgres.migration
python -m app.infrastructure.fastapi.main
```

### Run tests and lint

The tests use in-memory SQLite and mongomock, so no database has to be running.

```bash
pytest
ruff check . && ruff format --check .
```

---

## API

All routes are under `/api/v1`. Errors always have the same shape as the Go version:
`{"trace_id": "users-002", "message": "email or password is invalid"}`.

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/` | - | Health check: app name and version |
| POST | `/users/register` | - | Create a user (`201`, `409` if the email is taken) |
| POST | `/users/login` | - | Returns user plus `access` / `refresh` tokens |
| POST | `/users/refresh-token` | - | Rotates both tokens; the old ones stop working |
| POST | `/users/logout` | - | Revokes the session (`204`) |
| GET / POST | `/users/profile` | Bearer | Current user |
| GET | `/data/{slug}` | Bearer + admin | Paginated list. `_page`, `_pageSize`; other params are exact-match filters |
| GET | `/data/{slug}/{id}` | Bearer + admin | One row with its schema |
| GET | `/data/{slug}/describe` | Bearer + admin | Avro-style schema of the exposed fields |

Registered CRUD slugs: `users` (with `password` hidden) and `user-permissions`.
The registry is in [app/config/crud_models.py](app/config/crud_models.py).

Grant a user access to the CRUD API:

```sql
INSERT INTO user_permissions (user_id, permission, updated_at) VALUES (1, 'admin', now());
```

---

## Architecture

```
            ┌────────────────────────────────────────────┐
            │ infrastructure  FastAPI app, DI container,  │
            │                 DB connectors, migration    │
            │   ┌────────────────────────────────────┐   │
            │   │ interface   HTTP handlers,          │   │
            │   │             SQLAlchemy / Mongo repos │   │
            │   │   ┌────────────────────────────┐   │   │
            │   │   │ usecases   business rules   │   │   │
            │   │   │   ┌────────────────────┐   │   │   │
            │   │   │   │ domain  entities,   │   │   │   │
            │   │   │   │ errors, Protocols   │   │   │   │
            │   │   │   └────────────────────┘   │   │   │
            │   │   └────────────────────────────┘   │   │
            │   └────────────────────────────────────┘   │
            └────────────────────────────────────────────┘
                  imports only point inward  →  ●
```

| Layer | Folder | Contains | Depends on |
|---|---|---|---|
| Domain | `app/domain` | Pydantic entities, domain errors, repository/service **Protocols** | nothing (only Pydantic) |
| Usecases | `app/usecases` | `UserUsecase`, `CRUDUsecase` | domain only |
| Interface | `app/interface` | FastAPI routers, auth dependency, SQLAlchemy/Mongo repositories | usecases, domain |
| Infrastructure | `app/infrastructure` | `create_app`, `build_container`, engine/client creation, migration | everything (composition root) |
| Shared | `app/shared` | JWT and bcrypt implementations, slug/schema helpers | domain |
| Config | `app/config` | `Settings` (env vars), CRUD model registry | - |

### Request flow: `POST /api/v1/users/login`

1. `infrastructure/fastapi/main.py` builds the app. `build_container` wires
   `PostgresUserRepository`, `BcryptPasswordHasher` and `JWTAuthentication` into `UserUsecase`.
2. `interface/handlers/fastapi/user.py`: FastAPI validates the body as `UserLoginRequest`
   (invalid input returns `400 middleware-003`), then calls the usecase.
3. `usecases/user.py`: looks up the credential, verifies the bcrypt hash, signs an access
   and a refresh token, and stores them with `upsert_token`.
4. `interface/repositories/postgres/user.py`: SQLAlchemy reads and writes rows and returns
   **domain entities**, never ORM objects.
5. The handler returns `UserLoginResponse`. A domain error such as `InvalidCredentialsError`
   is mapped to `401 users-002`.

Protected routes use the `jwt_auth` dependency (`interface/handlers/fastapi/dependencies.py`).
It is the equivalent of the Go `JwtAuth` middleware. It verifies the JWT and also checks that
the token is still the one stored in the database, so logout and refresh revoke old tokens immediately.

### Go → Python mapping

| Go | Python |
|---|---|
| `src/domain/entities`, `src/domain/repositories` (interfaces) | `app/domain/entities`, `app/domain/repositories` (`typing.Protocol`) |
| `src/domain/models` (GORM structs) | `app/interface/repositories/postgres/models.py` (kept out of the domain) |
| `src/usecases/*` | `app/usecases/*` |
| `src/interface/handlers/gofiber` | `app/interface/handlers/fastapi` (router factories) |
| `src/interface/repositories/{postgres,mongodb}` | `app/interface/repositories/{postgres,mongodb}` |
| `src/infrastructure/gofiber/main.go` + `server/` | `app/infrastructure/fastapi/main.py` + `app/infrastructure/container.py` |
| `src/infrastructure/database/postgres/migration` | `app/infrastructure/database/postgres/migration.py` |
| koanf + `.env.dev` | pydantic-settings + `.env` (prefix `PYAPP_`) |
| swaggo comments | generated automatically by FastAPI at `/docs` |

---

## Design decisions

- **FastAPI over Django.** FastAPI does not impose a project layout or an ORM, so the clean
  architecture layers map one to one from the Go version. It also generates the OpenAPI docs
  that the Go project produced with swaggo.
- **`typing.Protocol` for ports.** Python Protocols are structural like Go interfaces: an
  adapter does not have to inherit from anything to satisfy them. Usecases are tested with
  an in-memory fake repository (`tests/fakes.py`).
- **Explicit dependency injection.** `build_container` wires every dependency in one place,
  the same way `main.go` does. Routers are built by factory functions that receive their
  usecase, so tests can swap the database (`create_app(settings, container)`).
- **Domain errors instead of HTTP errors in usecases.** Usecases raise `InvalidTokenError`,
  `NotFoundError`, etc. Only the handlers know about HTTP status codes and trace ids.
- **Sync SQLAlchemy.** Handlers are plain `def`, so FastAPI runs them in a threadpool. This
  keeps the code close to the Go version. bcrypt is CPU-bound and gains nothing from async.

## Fixes compared with the Go template

| # | Go template | This version |
|---|---|---|
| 1 | Refresh token uses `GOAPP_JWT_ACCESS_EXPIRES` | Uses its own `PYAPP_JWT_REFRESH_EXPIRES` |
| 2 | Issuer: result of `strings.Replace` is discarded | Spaces are replaced with `-` |
| 3 | Login errors differ for unknown email vs wrong password (email enumeration) | One message: `email or password is invalid` |
| 4 | `domain` imports `usecases`; `usecases/crud` imports `interface/repositories` | Dependencies point inward only; CRUD gets a repository **factory** via a Protocol |
| 5 | Any logged-in user can read every table through `/data`, including `user_tokens` | Requires `admin` permission; `user_tokens` not exposed; `password` hidden from data, filters and schema |
| 6 | List `total_data` = rows on the current page | Real `COUNT(*)` of all matching rows |
| 7 | List filters parsed but never applied | Filters applied, validated against exposed fields and converted to column types |
| 8 | Access token is not checked to be an access token | `sub` claim must match the expected token type |
| 9 | Two tokens issued in the same second are identical | `jti` makes every token unique |
| 10 | Swagger route registered twice, `/describe` reads a missing `:schema` param | Removed |

## Next steps

- Alembic migrations instead of `create_all`, so schema changes can be versioned.
- CRUD create/update/delete (still stubs in the Go template).
- Store one row per session in `user_tokens` to allow multiple devices per user.
- Rate limiting on `/users/login`.

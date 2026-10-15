"""Create the PostgreSQL tables.

Run with: python -m app.infrastructure.database.postgres.migration
"""

import logging

from app.config.settings import get_settings
from app.infrastructure.database.postgres.connector import create_database_engine
from app.interface.repositories.postgres.models import Base

logger = logging.getLogger(__name__)


def migrate() -> None:
    engine = create_database_engine(get_settings().sqlalchemy_url)
    logger.info("Start migration")
    Base.metadata.create_all(engine)
    for table_name in Base.metadata.tables:
        logger.info("Migrate table: %s", table_name)
    engine.dispose()
    logger.info("Migration success")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    migrate()

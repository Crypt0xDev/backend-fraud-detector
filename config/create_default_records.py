import logging

from sqlalchemy.orm import Session

from config.seeders.seed_admin import seed_admin
from config.seeders.seed_catalog import seed_catalog
from config.seeders.seed_legacy_roles import seed_legacy_roles
from config.seeders.seed_roles import seed_roles

logger = logging.getLogger(__name__)

SEEDERS = [seed_catalog, seed_roles, seed_legacy_roles, seed_admin]

def run_all_seeders(db: Session) -> None:
    for seeder in SEEDERS:
        try:
            seeder(db)
        except Exception:
            db.rollback()
            logger.exception("Falló el seeder %s", seeder.__name__)

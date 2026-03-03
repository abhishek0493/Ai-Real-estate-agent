#!/usr/bin/env python3
"""Seed the database with a demo tenant, properties, and prompt version.

Usage:
    docker compose exec backend python scripts/seed_db.py

Idempotent — safe to run multiple times.
"""

import sys
from pathlib import Path

# Ensure the backend root is on sys.path so `app.*` imports work
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.services.tenant_provisioning_service import TenantProvisioningService


def main() -> None:
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    session: Session = SessionLocal()

    print("=" * 60)
    print("  DATABASE SEED SCRIPT")
    print("=" * 60)

    try:
        service = TenantProvisioningService(session)
        tenant = service.provision_full(
            name="Demo Realty",
            email="demo@realty.com",
        )

        print()
        print(f"  Tenant Name : {tenant.name}")
        print(f"  Tenant ID   : {tenant.id}")
        print(f"  API Key     : {tenant.api_key}")
        print()
        print("  Test with:")
        print()
        print(f'  curl -X POST http://localhost:8000/api/v1/chat \\')
        print(f'    -H "X-Tenant-Key: {tenant.api_key}" \\')
        print(f'    -H "Content-Type: application/json" \\')
        print(f'    -d \'{{"message": "Looking for 2BHK in Andheri"}}\'')
        print()
        print("=" * 60)
        print("  SEED COMPLETE ✓")
        print("=" * 60)

    except Exception as e:
        session.rollback()
        print(f"\n  ERROR: {e}\n")
        sys.exit(1)
    finally:
        session.close()
        engine.dispose()


if __name__ == "__main__":
    main()

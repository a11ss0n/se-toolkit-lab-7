#!/usr/bin/env python3
"""Seed the database with test data for analytics endpoints.

Usage:
    cd backend && uv run python scripts/seed_data.py
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent / ".env.docker.secret")

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlmodel import SQLModel, select

from app.models.item import ItemRecord
from app.models.learner import Learner
from app.models.interaction import InteractionLog
from app.settings import Settings

settings = Settings()


async def seed_data():
    """Populate the database with realistic fixture data."""
    # Build database URL from settings
    db_url = (
        f"postgresql+asyncpg://{settings.db_user}:{settings.db_password}"
        f"@{settings.db_host}:{settings.db_port}/{settings.db_name}"
    )

    engine = create_async_engine(db_url, echo=False)

    async with engine.begin() as conn:
        # Create tables if not exist
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSession(engine) as session:
        # Check if data already exists
        result = await session.execute(select(ItemRecord).where(ItemRecord.type == "lab"))
        if result.first():
            print("Database already has data. Skipping seed.")
            return

        # Lab and tasks for Lab 04
        lab04 = ItemRecord(id=100, type="lab", title="Lab 04 — Testing, Front-end, and AI Agents", parent_id=None)
        task_setup = ItemRecord(id=101, type="task", title="Repository Setup", parent_id=100)
        task_backend = ItemRecord(id=102, type="task", title="Back-end Testing", parent_id=100)
        task_frontend = ItemRecord(id=103, type="task", title="Add Front-end", parent_id=100)
        session.add_all([lab04, task_setup, task_backend, task_frontend])

        # Lab 01
        lab01 = ItemRecord(id=200, type="lab", title="Lab 01 – Products, Architecture & Roles", parent_id=None)
        task1_1 = ItemRecord(id=201, type="task", title="Product & architecture description", parent_id=200)
        task1_2 = ItemRecord(id=202, type="task", title="Roles and skills mapping", parent_id=200)
        task1_3 = ItemRecord(id=203, type="task", title="Tech skills and the market", parent_id=200)
        session.add_all([lab01, task1_1, task1_2, task1_3])

        # Lab 02
        lab02 = ItemRecord(id=300, type="lab", title="Lab 02 — Run, Fix, and Deploy a Backend Service", parent_id=None)
        task2_1 = ItemRecord(id=301, type="task", title="Run the web server", parent_id=300)
        task2_2 = ItemRecord(id=302, type="task", title="Identify, report, and fix a bug", parent_id=300)
        task2_3 = ItemRecord(id=303, type="task", title="Run the web server using Docker Compose", parent_id=300)
        session.add_all([lab02, task2_1, task2_2, task2_3])

        # Learners from different groups
        learners = [
            Learner(id=1, external_id="stu001", student_group="B23-CS-01"),
            Learner(id=2, external_id="stu002", student_group="B23-CS-01"),
            Learner(id=3, external_id="stu003", student_group="B23-CS-02"),
            Learner(id=4, external_id="stu004", student_group="B23-CS-02"),
            Learner(id=5, external_id="stu005", student_group="B23-DS-01"),
            Learner(id=6, external_id="stu006", student_group="B23-CS-01"),
            Learner(id=7, external_id="stu007", student_group="B23-CS-02"),
            Learner(id=8, external_id="stu008", student_group="B23-DS-01"),
        ]
        session.add_all(learners)

        # Interactions for Lab 04
        interactions = [
            # task_setup (101): high scores
            InteractionLog(id=1, external_id=101, learner_id=1, item_id=101, kind="attempt", score=100.0, checks_passed=4, checks_total=4, created_at=datetime(2026, 2, 28, 10, 0)),
            InteractionLog(id=2, external_id=102, learner_id=2, item_id=101, kind="attempt", score=75.0, checks_passed=3, checks_total=4, created_at=datetime(2026, 2, 28, 11, 0)),
            InteractionLog(id=3, external_id=103, learner_id=3, item_id=101, kind="attempt", score=100.0, checks_passed=4, checks_total=4, created_at=datetime(2026, 2, 28, 14, 0)),
            InteractionLog(id=4, external_id=104, learner_id=4, item_id=101, kind="attempt", score=50.0, checks_passed=2, checks_total=4, created_at=datetime(2026, 3, 1, 9, 0)),
            InteractionLog(id=5, external_id=105, learner_id=5, item_id=101, kind="attempt", score=92.0, checks_passed=4, checks_total=4, created_at=datetime(2026, 3, 1, 10, 0)),
            InteractionLog(id=6, external_id=106, learner_id=6, item_id=101, kind="attempt", score=88.0, checks_passed=4, checks_total=4, created_at=datetime(2026, 3, 1, 11, 0)),
            
            # task_backend (102): mixed scores
            InteractionLog(id=7, external_id=107, learner_id=1, item_id=102, kind="attempt", score=80.0, checks_passed=4, checks_total=5, created_at=datetime(2026, 3, 1, 10, 0)),
            InteractionLog(id=8, external_id=108, learner_id=2, item_id=102, kind="attempt", score=20.0, checks_passed=1, checks_total=5, created_at=datetime(2026, 3, 1, 11, 0)),
            InteractionLog(id=9, external_id=109, learner_id=3, item_id=102, kind="attempt", score=60.0, checks_passed=3, checks_total=5, created_at=datetime(2026, 3, 2, 10, 0)),
            InteractionLog(id=10, external_id=110, learner_id=7, item_id=102, kind="attempt", score=71.4, checks_passed=5, checks_total=7, created_at=datetime(2026, 3, 2, 11, 0)),
            
            # task_frontend (103): lower scores
            InteractionLog(id=11, external_id=111, learner_id=4, item_id=103, kind="attempt", score=0.0, checks_passed=0, checks_total=3, created_at=datetime(2026, 3, 2, 15, 0)),
            InteractionLog(id=12, external_id=112, learner_id=5, item_id=103, kind="attempt", score=33.3, checks_passed=1, checks_total=3, created_at=datetime(2026, 3, 2, 16, 0)),
            InteractionLog(id=13, external_id=113, learner_id=8, item_id=103, kind="attempt", score=66.7, checks_passed=2, checks_total=3, created_at=datetime(2026, 3, 3, 10, 0)),

            # Interactions for Lab 01
            InteractionLog(id=14, external_id=114, learner_id=1, item_id=201, kind="attempt", score=90.0, checks_passed=9, checks_total=10, created_at=datetime(2026, 3, 3, 11, 0)),
            InteractionLog(id=15, external_id=115, learner_id=2, item_id=201, kind="attempt", score=85.0, checks_passed=8, checks_total=10, created_at=datetime(2026, 3, 3, 12, 0)),
            InteractionLog(id=16, external_id=116, learner_id=3, item_id=201, kind="attempt", score=92.1, checks_passed=9, checks_total=10, created_at=datetime(2026, 3, 3, 13, 0)),
            
            InteractionLog(id=17, external_id=117, learner_id=4, item_id=202, kind="attempt", score=78.0, checks_passed=7, checks_total=9, created_at=datetime(2026, 3, 4, 10, 0)),
            InteractionLog(id=18, external_id=118, learner_id=5, item_id=202, kind="attempt", score=82.0, checks_passed=8, checks_total=10, created_at=datetime(2026, 3, 4, 11, 0)),
            
            InteractionLog(id=19, external_id=119, learner_id=6, item_id=203, kind="attempt", score=70.0, checks_passed=7, checks_total=10, created_at=datetime(2026, 3, 4, 12, 0)),
            InteractionLog(id=20, external_id=120, learner_id=7, item_id=203, kind="attempt", score=65.0, checks_passed=6, checks_total=9, created_at=datetime(2026, 3, 4, 13, 0)),

            # Interactions for Lab 02
            InteractionLog(id=21, external_id=121, learner_id=1, item_id=301, kind="attempt", score=95.0, checks_passed=19, checks_total=20, created_at=datetime(2026, 3, 5, 10, 0)),
            InteractionLog(id=22, external_id=122, learner_id=2, item_id=301, kind="attempt", score=88.0, checks_passed=17, checks_total=20, created_at=datetime(2026, 3, 5, 11, 0)),
            
            InteractionLog(id=23, external_id=123, learner_id=3, item_id=302, kind="attempt", score=71.4, checks_passed=5, checks_total=7, created_at=datetime(2026, 3, 5, 12, 0)),
            InteractionLog(id=24, external_id=124, learner_id=4, item_id=302, kind="attempt", score=57.1, checks_passed=4, checks_total=7, created_at=datetime(2026, 3, 5, 13, 0)),
            
            InteractionLog(id=25, external_id=125, learner_id=5, item_id=303, kind="attempt", score=100.0, checks_passed=3, checks_total=3, created_at=datetime(2026, 3, 5, 14, 0)),
            InteractionLog(id=26, external_id=126, learner_id=6, item_id=303, kind="attempt", score=66.7, checks_passed=2, checks_total=3, created_at=datetime(2026, 3, 5, 15, 0)),
        ]
        session.add_all(interactions)

        await session.commit()
        print("Database seeded successfully!")
        print(f"  - Labs: 3 (Lab 01, Lab 02, Lab 04)")
        print(f"  - Tasks: 9")
        print(f"  - Learners: {len(learners)}")
        print(f"  - Interactions: {len(interactions)}")


if __name__ == "__main__":
    asyncio.run(seed_data())

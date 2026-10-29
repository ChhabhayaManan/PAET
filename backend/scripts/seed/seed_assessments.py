"""Seed the verified assessment bank, inside the backend container:

    docker compose exec backend python -m scripts.seed.seed_assessments

Re-verifies every item by execution first; rerunning is safe (upsert by external_id)."""

import json
import pathlib

from app.core.database import SessionLocal
from app.features.practice.logic.assessment.seeding import seed

BANK = pathlib.Path(__file__).resolve().parents[2] / "app" / "data" / "assessments.json"


def main() -> None:
    bank = json.loads(BANK.read_text("utf-8"))
    with SessionLocal() as db:
        report = seed(db, bank)
    for key, count in sorted(report.items()):
        print(f"  {count:3d}  {key}")


if __name__ == "__main__":
    main()

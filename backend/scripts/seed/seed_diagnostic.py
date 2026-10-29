"""Load the verified diagnostic bank into diagnostic_items, inside the backend container:

    docker compose -f docker-compose.yml -f docker-compose.local.yml exec backend python -m scripts.seed.seed_diagnostic

Reads app/data/diagnostic.json (written by scripts.generate.generate_diagnostic). Rerunning is safe:
rows are upserted by external_id and an unchanged row keeps its review. A reviewed row
whose kind, body or key changed goes back to unreviewed, since only what a human checked
is served. Approve rows with scripts.tools.review_diagnostic."""

import json
import pathlib
from collections import Counter

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.features.onboarding.models import DiagnosticItem
from scripts._local_db import require_local_db

BANK = pathlib.Path(__file__).resolve().parents[2] / "app" / "data" / "diagnostic.json"
COLUMNS = ("kind", "topic", "tier", "difficulty", "language", "concept_key", "body", "key")
CONTENT = ("kind", "body", "key")


def external_id(item: dict) -> str:
    return f"{item['concept_key']}:{item['language']}"


def load(db: Session, items: list[dict]) -> Counter:
    report: Counter = Counter()
    rows = {row.external_id: row for row in db.query(DiagnosticItem)}
    for item in items:
        eid = external_id(item)
        row = rows.get(eid)
        if row is None:
            row = rows[eid] = DiagnosticItem(external_id=eid, reviewed=False)
            db.add(row)
            report["inserted"] += 1
        elif all(getattr(row, column) == item[column] for column in COLUMNS):
            report["unchanged"] += 1
            continue
        elif row.reviewed and any(getattr(row, c) != item[c] for c in CONTENT):
            row.reviewed = False
            report["updated_was_reviewed"] += 1
        else:
            report["updated"] += 1
        for column in COLUMNS:
            setattr(row, column, item[column])
    db.commit()
    return report


def main() -> None:
    require_local_db()
    items = json.loads(BANK.read_text("utf-8"))["items"]
    with SessionLocal() as db:
        report = load(db, items)
    for key, count in sorted(report.items()):
        print(f"  {count:3d}  {key}")


if __name__ == "__main__":
    main()

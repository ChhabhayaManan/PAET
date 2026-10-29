"""Run once, inside the backend container (the executor is on an internal network):

    docker compose exec backend python -m scripts.generate.generate_assessments

Writes app/data/assessments.json. Raw model replies are cached in
app/data/assessments_raw.json; pass --refresh to pay for new drafts, or
--refresh-key mcq:loops to redraft one topic."""

import argparse
import json
import pathlib

from app.core.database import SessionLocal
from app.features.practice.logic.assessment.generation import RawCache, generate

DATA = pathlib.Path(__file__).resolve().parents[2] / "app" / "data"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--refresh-key", action="append", default=[],
                        help="redraft one cached reply, e.g. mcq:loops")
    args = parser.parse_args()

    cache = RawCache(DATA / "assessments_raw.json", refresh=args.refresh)
    for key in args.refresh_key:
        cache.data.pop(key, None)
    with SessionLocal() as db:
        result = generate(db, cache)

    log = result.pop("log")
    (DATA / "assessments.json").write_text(json.dumps(result, indent=2), "utf-8")
    print(f"mcqs={len(result['mcqs'])} diagnostic={len(result['diagnostic'])} "
          f"debug={len(result['debug'])}")
    for reason, count in sorted(log.items()):
        print(f"  {count:3d}  {reason}")


if __name__ == "__main__":
    main()

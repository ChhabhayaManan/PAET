"""Wipe and re-register ONE demo account before a rehearsal, inside the backend container:

    docker compose exec backend python -m scripts.tools.reset_demo_user --email demo@example.com

Defaults to DEV_LOGIN_EMAIL so the login page's dev button signs straight into it. Only
the named account is touched."""

import argparse

from app.core.config import settings
from app.core.database import SessionLocal
from app.features.learner_model.logic.demo import reset_account


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", default=settings.DEV_LOGIN_EMAIL)
    parser.add_argument("--username", default=None)
    parser.add_argument("--password", default="DemoPass123!")
    args = parser.parse_args()
    if not args.email:
        parser.error("no --email given and DEV_LOGIN_EMAIL is not set")

    username = args.username or args.email.split("@")[0].replace(".", "_")
    with SessionLocal() as db:
        user = reset_account(db, args.email, username, args.password)
    print(f"reset {user.email} (id {user.id}); password {args.password}")


if __name__ == "__main__":
    main()

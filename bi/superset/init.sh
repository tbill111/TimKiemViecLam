#!/bin/sh
set -eu
superset db upgrade
python - <<'PY'
import os

from superset.app import create_app
from superset.extensions import db
from sqlalchemy.engine import URL

admin_user = os.environ.get("SUPERSET_ADMIN_USER", "admin")
admin_email = os.environ.get("SUPERSET_ADMIN_EMAIL", "admin@smartcareer.vn")
admin_password = os.environ["SUPERSET_ADMIN_PASSWORD"]
database_name = os.environ.get("BI_SUPERSET_DATABASE_NAME", "SmartCareer")
database_uri = URL.create(
    "postgresql+psycopg2",
    username=os.environ["BI_DATABASE_USER"],
    password=os.environ["BI_READER_PASSWORD"],
    host=os.environ.get("BI_DATABASE_HOST", "db"),
    port=int(os.environ.get("BI_DATABASE_PORT", "5432")),
    database=os.environ["BI_DATABASE_NAME"],
).render_as_string(hide_password=False)

app = create_app()
with app.app_context():
    from superset.models.core import Database

    security_manager = app.appbuilder.sm
    if security_manager.find_user(username=admin_user) is None:
        admin_role = security_manager.find_role("Admin")
        if admin_role is None:
            raise RuntimeError("Superset Admin role is missing after `superset db upgrade`.")
        if not security_manager.add_user(
            username=admin_user,
            first_name="SmartCareer",
            last_name="Admin",
            email=admin_email,
            role=admin_role,
            password=admin_password,
        ):
            raise RuntimeError(f"Failed to create Superset admin user {admin_user!r}.")

    database = db.session.query(Database).filter_by(database_name=database_name).one_or_none()
    if database is None:
        database = Database(database_name=database_name, sqlalchemy_uri=database_uri)
    else:
        database.sqlalchemy_uri = database_uri
    db.session.add(database)
    db.session.commit()
print(f"Superset admin '{admin_user}' and database connection '{database_name}' are configured.")
PY
superset init
exec superset run -h 0.0.0.0 -p 8088 --with-threads

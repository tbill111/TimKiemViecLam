# Superset handoff

The Compose service starts Superset 4.1.2 at `http://localhost:${SUPERSET_PORT:-8088}`. The local demo administrator is `admin` / the value of `SUPERSET_ADMIN_PASSWORD` (default `admin_demo_password`). `superset_meta` stores Superset metadata; the SmartCareer PostgreSQL schema remains separate. On startup, `init.sh` creates or updates a Superset database connection named `SmartCareer` using the BI connection environment variables; no manual database connection setup is required.

The connection uses `BI_DATABASE_USER` (default `bi_reader`) and `BI_READER_PASSWORD` from the Compose environment. It targets `POSTGRES_DB` on service `db`; SQLAlchemy constructs the URI so passwords containing reserved URL characters are handled correctly.

`bi_reader` is provisioned by the database/migration with `SELECT` on only `v_skill_supply_demand`, `v_salary`, `v_funnel`, and `v_funnel_stages`. Create datasets for those four views. Build the dashboard charts from the views; funnel charts must use `v_funnel_stages` for stage-by-stage counts. Export the finished dashboard from Superset as `dashboard_export.zip` and commit it here.

For embedding, open the dashboard's Embed settings and allow `http://localhost:8080` and `http://localhost:5173`. Put the dashboard UUID plus the integer dataset IDs for `v_funnel` and `v_funnel_stages` into `.env` as `SUPERSET_DASHBOARD_ID`, `SUPERSET_FUNNEL_DATASET_ID`, and `SUPERSET_FUNNEL_STAGES_DATASET_ID`. The API intentionally returns 503 to recruiters until both company-scoped datasets are configured. Do not use an unfiltered token as a fallback.

To validate both company scopes after the dashboard and chart are ready, run `python scripts/check_bi_views.py`; see `--help` for the API and PostgreSQL URLs. The script also compares all four SQL views to the BI API responses.

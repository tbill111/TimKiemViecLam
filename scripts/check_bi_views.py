"""Compare the four PostgreSQL BI views to their API endpoints and fetch a guest token."""
from __future__ import annotations

import argparse
import json
import os
from decimal import Decimal
from datetime import date, datetime

import psycopg
import requests


def serial(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def rows_from_sql(connection, view: str, company_id: int | None = None):
    with connection.cursor() as cursor:
        if view in {"v_funnel", "v_funnel_stages"} and company_id is not None:
            cursor.execute(f"SELECT * FROM {view} WHERE company_id = %s ORDER BY 1, 2", (company_id,))
        else:
            cursor.execute(f"SELECT * FROM {view} ORDER BY 1, 2")
        names = [column.name for column in cursor.description]
        return [dict(zip(names, map(serial, row))) for row in cursor.fetchall()]


def normalized(items):
    return sorted(json.dumps(item, sort_keys=True, ensure_ascii=False, default=serial) for item in items)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-base", default=os.getenv("API_BASE_URL", "http://localhost:8000/api"))
    parser.add_argument("--db-url", default=os.getenv("DATABASE_URL", "postgresql://smartcareer:smartcareer_demo_password@localhost:5432/smartcareer"))
    parser.add_argument("--email", default=os.getenv("BI_CHECK_EMAIL", "hr1@smartcareer.vn"))
    parser.add_argument("--password", default=os.getenv("BI_CHECK_PASSWORD", "Demo@12345"))
    args = parser.parse_args()
    session = requests.Session()
    login = session.post(f"{args.api_base}/auth/login", json={"email": args.email, "password": args.password}, timeout=20)
    login.raise_for_status()
    bearer = login.json()["access_token"]
    user = login.json()["user"]
    headers = {"Authorization": f"Bearer {bearer}"}
    api_skills = session.get(f"{args.api_base}/bi/skills", headers=headers, timeout=20).json()["items"]
    api_salary = session.get(f"{args.api_base}/bi/salary", headers=headers, timeout=20).json()["items"]
    api_funnel = session.get(f"{args.api_base}/bi/funnel", headers=headers, timeout=20).json()
    with psycopg.connect(args.db_url) as connection:
        direct = {
            "v_skill_supply_demand": rows_from_sql(connection, "v_skill_supply_demand"),
            "v_salary": rows_from_sql(connection, "v_salary"),
            "v_funnel": rows_from_sql(connection, "v_funnel", user.get("company_id")),
            "v_funnel_stages": rows_from_sql(connection, "v_funnel_stages", user.get("company_id")),
        }
    checks = {
        "v_skill_supply_demand": normalized(api_skills) == normalized(direct["v_skill_supply_demand"]),
        "v_salary": normalized(api_salary) == normalized(direct["v_salary"]),
        "v_funnel": normalized(api_funnel["items"]) == normalized(direct["v_funnel"]),
        "v_funnel_stages": normalized(api_funnel["stages"]) == normalized(direct["v_funnel_stages"]),
    }
    token_response = session.get(f"{args.api_base}/bi/guest-token", headers=headers, timeout=20)
    guest = token_response.json() if token_response.ok else {"error": token_response.json()}
    output = {"token": guest.get("token"), "dashboard_id": guest.get("dashboard_id"), "superset_domain": guest.get("superset_domain"), "view_checks": checks}
    print(json.dumps(output, ensure_ascii=False, indent=2))
    if not all(checks.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()

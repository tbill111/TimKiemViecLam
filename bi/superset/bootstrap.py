"""Tự dựng dashboard "Thị trường tuyển dụng" trên Superset bằng REST API (chạy lặp lại không tạo trùng).

    python bi/superset/bootstrap.py --url http://localhost:8091 [--write-env .env]

Tạo: kết nối CSDL (role bi_reader), 4 dataset từ view, 6 biểu đồ (2, 4, 6 bắt buộc + 1, 3, 8), dashboard, bật nhúng.
In ra SUPERSET_DASHBOARD_ID và SUPERSET_RLS_DATASET_IDS để điền vào .env (hoặc dùng --write-env).
Native Filter không tạo tự động; thêm bằng giao diện nếu cần.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import httpx

DB_NAME = "SmartCareer BI"
DASHBOARD_SLUG = "thi-truong-tuyen-dung"
VIEWS = ["v_skill_supply_demand", "v_salary", "v_funnel", "v_funnel_stages"]
RLS_VIEWS = ["v_funnel", "v_funnel_stages"]  # có cột company_id


def simple(col: str, agg: str, label: str) -> dict:
    return {"expressionType": "SIMPLE", "column": {"column_name": col}, "aggregate": agg, "label": label}


def sql(expr: str, label: str) -> dict:
    return {"expressionType": "SQL", "sqlExpression": expr, "label": label}


def charts(ds: dict[str, int]) -> list[dict]:
    """(tên, viz_type, view, params) – số thứ tự theo bảng ở bi/README.md."""
    d = lambda view: f"{ds[view]}__table"  # noqa: E731
    common = {"adhoc_filters": [], "row_limit": 1000}
    return [
        {"name": "1. Hồ sơ đã nộp", "viz": "big_number_total", "view": "v_funnel", "w": 3,
         "params": {"metric": sql("COUNT(*)", "Hồ sơ đã nộp"), **common}},
        {"name": "1b. Tỷ lệ tuyển", "viz": "big_number_total", "view": "v_funnel", "w": 3,
         "params": {"metric": sql("AVG(hired::int)", "Tỷ lệ tuyển"), "y_axis_format": ",.1%", **common}},
        {"name": "2. Top 15 kỹ năng theo số ứng viên", "viz": "echarts_timeseries_bar", "view": "v_skill_supply_demand", "w": 6,
         "params": {"x_axis": "skill", "metrics": [simple("so_ung_vien", "MAX", "Số ứng viên")], "groupby": [], "orientation": "vertical",
                    "x_axis_sort": "Số ứng viên", "x_axis_sort_asc": False, **{**common, "row_limit": 15}}},
        {"name": "3. Cung so với cầu theo kỹ năng", "viz": "echarts_timeseries_bar", "view": "v_skill_supply_demand", "w": 6,
         "params": {"x_axis": "skill", "metrics": [simple("so_ung_vien", "MAX", "Số ứng viên"), simple("so_tin_yeu_cau", "MAX", "Số tin yêu cầu")],
                    "groupby": [], "orientation": "vertical", "x_axis_sort": "Số ứng viên", "x_axis_sort_asc": False, **{**common, "row_limit": 15}}},
        {"name": "4. Lương trung bình theo tháng và cấp bậc", "viz": "echarts_timeseries_line", "view": "v_salary", "w": 6,
         "params": {"x_axis": "thang", "time_grain_sqla": "P1M", "metrics": [simple("luong_tb", "AVG", "Lương TB (triệu VNĐ/tháng)")],
                    "groupby": ["level"], **common}},
        {"name": "6. Phễu tuyển dụng", "viz": "funnel", "view": "v_funnel_stages", "w": 6,
         "params": {"groupby": ["giai_doan"], "metric": simple("so_ho_so", "SUM", "Số hồ sơ"), "sort_by_metric": True, "show_labels": True, **{**common, "row_limit": 10}}},
        {"name": "8. Tỷ lệ được tuyển theo nhóm điểm khớp", "viz": "echarts_timeseries_bar", "view": "v_funnel", "w": 6,
         "params": {"x_axis": "nhom_diem", "metrics": [sql("AVG(hired::int)", "Tỷ lệ tuyển")], "groupby": [], "orientation": "vertical",
                    "y_axis_format": ",.1%", **common}},
    ]


class Superset:
    def __init__(self, base: str, user: str, password: str):
        self.c = httpx.Client(base_url=base, timeout=60, follow_redirects=True)
        # Superset 4.1: một số API ghi (dashboard, chart) cần người dùng từ phiên đăng nhập (cookie), ngoài Bearer
        self.c.post("/login/", data={"username": user, "password": password}).raise_for_status()
        r = self.c.post("/api/v1/security/login", json={"username": user, "password": password, "provider": "db", "refresh": True})
        r.raise_for_status()
        self.c.headers["Authorization"] = f"Bearer {r.json()['access_token']}"

    def call(self, method: str, path: str, **kw):
        r = self.c.request(method, path, **kw)
        if r.status_code >= 400:
            raise RuntimeError(f"{method} {path} → {r.status_code}: {r.text[:400]}")
        return r.json()

    def find(self, path: str, col: str, value: str) -> int | None:
        q = json.dumps({"filters": [{"col": col, "opr": "eq", "value": value}]})
        res = self.call("GET", path, params={"q": q})["result"]
        return res[0]["id"] if res else None


def position(chart_ids: list[tuple[int, str, int]]) -> dict:
    """Bố cục 12 cột: các biểu đồ rộng 3/6 xếp hàng ngang."""
    layout: dict = {"DASHBOARD_VERSION_KEY": "v2", "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
                    "GRID_ID": {"type": "GRID", "id": "GRID_ID", "children": [], "parents": ["ROOT_ID"]}}
    rows: list[list[tuple[int, str, int]]] = [[]]
    for item in chart_ids:
        if sum(w for _, _, w in rows[-1]) + item[2] > 12:
            rows.append([])
        rows[-1].append(item)
    for r, row in enumerate(rows, start=1):
        rid = f"ROW-{r}"
        layout["GRID_ID"]["children"].append(rid)
        layout[rid] = {"type": "ROW", "id": rid, "children": [], "parents": ["ROOT_ID", "GRID_ID"], "meta": {"background": "BACKGROUND_TRANSPARENT"}}
        for chart_id, name, width in row:
            cid = f"CHART-{chart_id}"
            layout[rid]["children"].append(cid)
            layout[cid] = {"type": "CHART", "id": cid, "children": [], "parents": ["ROOT_ID", "GRID_ID", rid],
                           "meta": {"chartId": chart_id, "width": width, "height": 40, "sliceName": name}}
    return layout


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8088")
    ap.add_argument("--user", default="admin")
    ap.add_argument("--password", default="admin")
    ap.add_argument("--bi-reader-password", default="bi_reader_pw")
    ap.add_argument("--db-host", default="db:5432", help="địa chỉ PostgreSQL nhìn từ container Superset")
    ap.add_argument("--db-name", default="smartcareer")
    ap.add_argument("--domains", default="http://localhost:8080,http://localhost:5173")
    ap.add_argument("--write-env", type=Path, default=None)
    args = ap.parse_args()

    s = Superset(args.url, args.user, args.password)

    db_id = s.find("/api/v1/database/", "database_name", DB_NAME)
    if db_id is None:
        uri = f"postgresql+psycopg2://bi_reader:{args.bi_reader_password}@{args.db_host}/{args.db_name}"
        db_id = s.call("POST", "/api/v1/database/", json={"database_name": DB_NAME, "sqlalchemy_uri": uri, "expose_in_sqllab": True})["id"]
    print(f"database id={db_id}")

    ds: dict[str, int] = {}
    for view in VIEWS:
        q = json.dumps({"filters": [{"col": "table_name", "opr": "eq", "value": view}]})
        found = s.call("GET", "/api/v1/dataset/", params={"q": q})["result"]
        ds[view] = found[0]["id"] if found else s.call("POST", "/api/v1/dataset/", json={"database": db_id, "schema": "public", "table_name": view})["id"]
        print(f"dataset {view} id={ds[view]}")

    dash_id = s.find("/api/v1/dashboard/", "slug", DASHBOARD_SLUG)
    if dash_id is None:
        dash_id = s.call("POST", "/api/v1/dashboard/", json={"dashboard_title": "Thị trường tuyển dụng", "slug": DASHBOARD_SLUG, "published": True})["id"]
    print(f"dashboard id={dash_id}")

    placed: list[tuple[int, str, int]] = []
    for spec in charts(ds):
        existing = s.find("/api/v1/chart/", "slice_name", spec["name"])
        params = {"viz_type": spec["viz"], "datasource": f"{ds[spec['view']]}__table", **spec["params"]}
        body = {"slice_name": spec["name"], "viz_type": spec["viz"], "datasource_id": ds[spec["view"]], "datasource_type": "table",
                "params": json.dumps(params), "dashboards": [dash_id]}
        if existing is None:
            existing = s.call("POST", "/api/v1/chart/", json=body)["id"]
        else:
            s.call("PUT", f"/api/v1/chart/{existing}", json=body)
        placed.append((existing, spec["name"], spec["w"]))
        print(f"chart {spec['name']} id={existing}")

    s.call("PUT", f"/api/v1/dashboard/{dash_id}", json={"position_json": json.dumps(position(placed)), "published": True,
                                                         "json_metadata": json.dumps({"refresh_frequency": 0})})
    emb = s.call("POST", f"/api/v1/dashboard/{dash_id}/embedded", json={"allowed_domains": [d for d in args.domains.split(",") if d]})
    uuid = emb["result"]["uuid"]
    rls = ",".join(str(ds[v]) for v in RLS_VIEWS)
    print(f"\nSUPERSET_DASHBOARD_ID={uuid}\nSUPERSET_RLS_DATASET_IDS={rls}")

    if args.write_env:
        text = args.write_env.read_text(encoding="utf-8") if args.write_env.exists() else ""
        for key, value in (("SUPERSET_DASHBOARD_ID", uuid), ("SUPERSET_RLS_DATASET_IDS", rls)):
            if re.search(rf"^{key}=.*$", text, flags=re.M):
                text = re.sub(rf"^{key}=.*$", f"{key}={value}", text, flags=re.M)
            else:
                text += f"\n{key}={value}"
        args.write_env.write_text(text, encoding="utf-8")
        print(f"Đã cập nhật {args.write_env}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Tự dựng dashboard "Thị trường tuyển dụng" trên Superset bằng REST API (chạy lặp lại không tạo trùng).

    python bi/superset/bootstrap.py --url http://localhost:8088 --password <SUPERSET_ADMIN_PASSWORD> [--write-env .env]

Dùng kết nối CSDL "SmartCareer" do `init.sh` tạo (role chỉ đọc `bi_reader`). Tạo 4 dataset từ view `v_*`, 6 biểu đồ
(2, 3, 4, 6 theo bảng chỉ số của đề cộng 2 thẻ số tổng quan), dashboard và bật nhúng. In ra và (nếu có --write-env) ghi vào .env:
SUPERSET_DASHBOARD_ID (UUID nhúng), SUPERSET_FUNNEL_DATASET_ID, SUPERSET_FUNNEL_STAGES_DATASET_ID (dataset có cột company_id,
dùng cho Row Level Security trong guest token). Sau đó khởi động lại `api` để nhận biến mới.
Native Filter không tạo tự động; thêm bằng giao diện Superset nếu cần.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import httpx

DB_NAME = "SmartCareer"
DASHBOARD_TITLE = "Thị trường tuyển dụng"
DASHBOARD_SLUG = "thi-truong-tuyen-dung"
VIEWS = ["v_skill_supply_demand", "v_salary", "v_funnel", "v_funnel_stages"]


def simple(col: str, agg: str, label: str) -> dict:
    return {"expressionType": "SIMPLE", "column": {"column_name": col}, "aggregate": agg, "label": label}


def sql(expr: str, label: str) -> dict:
    return {"expressionType": "SQL", "sqlExpression": expr, "label": label}


def charts() -> list[dict]:
    """(tên, viz_type, view, độ rộng, params). Số thứ tự biểu đồ theo bảng chỉ số của đề (2, 3, 4, 6)."""
    common = {"adhoc_filters": [], "row_limit": 1000}
    return [
        {"name": "1. Hồ sơ đã nộp", "viz": "big_number_total", "view": "v_funnel", "w": 3,
         "params": {"metric": simple("applied", "SUM", "Hồ sơ đã nộp"), **common}},
        {"name": "1b. Tỷ lệ được tuyển", "viz": "big_number_total", "view": "v_funnel", "w": 3,
         "params": {"metric": sql("SUM(hired)::float / NULLIF(SUM(applied), 0)", "Tỷ lệ được tuyển"), "y_axis_format": ",.1%", **common}},
        {"name": "2. Top 15 kỹ năng theo số ứng viên", "viz": "echarts_timeseries_bar", "view": "v_skill_supply_demand", "w": 6,
         "params": {"x_axis": "skill_name", "metrics": [simple("candidate_count", "MAX", "Số ứng viên")], "groupby": [], "orientation": "vertical",
                    "x_axis_sort": "Số ứng viên", "x_axis_sort_asc": False, **{**common, "row_limit": 15}}},
        {"name": "3. Cung so với cầu theo kỹ năng", "viz": "echarts_timeseries_bar", "view": "v_skill_supply_demand", "w": 6,
         "params": {"x_axis": "skill_name", "metrics": [simple("candidate_count", "MAX", "Số ứng viên"), simple("open_job_count", "MAX", "Số tin đang cần")],
                    "groupby": [], "orientation": "vertical", "x_axis_sort": "Số ứng viên", "x_axis_sort_asc": False, **{**common, "row_limit": 15}}},
        {"name": "4. Lương trung bình theo tháng và cấp bậc", "viz": "echarts_timeseries_line", "view": "v_salary", "w": 6,
         "params": {"x_axis": "posted_month", "time_grain_sqla": "P1M",
                    "metrics": [sql("SUM((average_salary_min + average_salary_max) / 2 * job_count) / NULLIF(SUM(job_count), 0)", "Lương TB (triệu VNĐ/tháng)")],
                    "groupby": ["level"], **common}},
        {"name": "6. Phễu tuyển dụng", "viz": "funnel", "view": "v_funnel_stages", "w": 6,
         "params": {"groupby": ["stage"], "metric": simple("applications", "SUM", "Số hồ sơ từng đạt bước"), "sort_by_metric": True, "show_labels": True,
                    "adhoc_filters": [{"expressionType": "SIMPLE", "clause": "WHERE", "subject": "stage", "operator": "!=", "comparator": "rejected"}],
                    "row_limit": 10}},
    ]


class Superset:
    def __init__(self, base: str, user: str, password: str):
        self.c = httpx.Client(base_url=base, timeout=60, follow_redirects=True)
        # Superset 4.1: một số API ghi (dashboard, chart) cần người dùng từ phiên đăng nhập (cookie), ngoài Bearer
        self.c.post("/login/", data={"username": user, "password": password}).raise_for_status()
        r = self.c.post("/api/v1/security/login", json={"username": user, "password": password, "provider": "db", "refresh": True})
        r.raise_for_status()
        self.c.headers["Authorization"] = f"Bearer {r.json()['access_token']}"
        # Khi phiên cookie có mặt, các lệnh ghi bị kiểm tra CSRF (WTF_CSRF_ENABLED): lấy token và gửi kèm.
        csrf = self.c.get("/api/v1/security/csrf_token/")
        csrf.raise_for_status()
        self.c.headers["X-CSRFToken"] = csrf.json()["result"]
        self.c.headers["Referer"] = base

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


def set_env(path: Path, values: dict[str, str]) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    for key, value in values.items():
        if re.search(rf"^{key}=.*$", text, flags=re.M):
            text = re.sub(rf"^{key}=.*$", f"{key}={value}", text, flags=re.M)
        else:
            text += ("\n" if text and not text.endswith("\n") else "") + f"{key}={value}\n"
    path.write_text(text, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", default="http://localhost:8088")
    ap.add_argument("--user", default="admin")
    ap.add_argument("--password", default="admin_demo_password", help="SUPERSET_ADMIN_PASSWORD trong .env")
    ap.add_argument("--domains", default="http://localhost:8080,http://localhost:5173", help="các nguồn được phép nhúng dashboard (CSP frame-ancestors)")
    ap.add_argument("--write-env", type=Path, default=None)
    ap.add_argument("--export-zip", type=Path, default=None, help="xuất dashboard ra tệp .zip (nhập lại được bằng Superset: Dashboards → Import)")
    args = ap.parse_args()

    s = Superset(args.url, args.user, args.password)

    db_id = s.find("/api/v1/database/", "database_name", DB_NAME)
    if db_id is None:
        raise SystemExit(f"Chưa có kết nối CSDL '{DB_NAME}': khởi động service superset (init.sh tạo kết nối này) rồi chạy lại.")
    print(f"database id={db_id}")

    ds: dict[str, int] = {}
    for view in VIEWS:
        q = json.dumps({"filters": [{"col": "table_name", "opr": "eq", "value": view}]})
        found = s.call("GET", "/api/v1/dataset/", params={"q": q})["result"]
        ds[view] = found[0]["id"] if found else s.call("POST", "/api/v1/dataset/", json={"database": db_id, "schema": "public", "table_name": view})["id"]
        print(f"dataset {view} id={ds[view]}")

    dash_id = s.find("/api/v1/dashboard/", "slug", DASHBOARD_SLUG)
    if dash_id is None:
        dash_id = s.call("POST", "/api/v1/dashboard/", json={"dashboard_title": DASHBOARD_TITLE, "slug": DASHBOARD_SLUG, "published": True})["id"]
    print(f"dashboard id={dash_id}")

    placed: list[tuple[int, str, int]] = []
    for spec in charts():
        ds_id = ds[spec["view"]]
        existing = s.find("/api/v1/chart/", "slice_name", spec["name"])
        params = {"viz_type": spec["viz"], "datasource": f"{ds_id}__table", **spec["params"]}
        body = {"slice_name": spec["name"], "viz_type": spec["viz"], "datasource_id": ds_id, "datasource_type": "table",
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
    values = {"SUPERSET_DASHBOARD_ID": uuid, "SUPERSET_FUNNEL_DATASET_ID": str(ds["v_funnel"]),
              "SUPERSET_FUNNEL_STAGES_DATASET_ID": str(ds["v_funnel_stages"])}
    print("\n" + "\n".join(f"{k}={v}" for k, v in values.items()))
    if args.export_zip:
        r = s.c.get("/api/v1/dashboard/export/", params={"q": f"!({dash_id})"})
        r.raise_for_status()
        args.export_zip.parent.mkdir(parents=True, exist_ok=True)
        args.export_zip.write_bytes(r.content)
        print(f"Đã xuất {args.export_zip} ({len(r.content)} byte)")
    if args.write_env:
        set_env(args.write_env, values)
        print(f"Đã cập nhật {args.write_env}; chạy `docker compose up -d api` để api nhận biến mới.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

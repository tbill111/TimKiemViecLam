"""Đối chiếu view PostgreSQL thật với API /api/bi/* (cùng định nghĩa chỉ số).

Cần stack đang chạy: docker compose up -d db api. Chạy: python scripts/check_bi_views.py
Thoát với mã 1 nếu có số liệu lệch.
"""
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

API = "http://localhost:8000/api"


def psql(sql: str, user="smartcareer", db="smartcareer", pw=None) -> list[list[str]]:
    cmd = ["docker", "compose", "exec", "-T"]
    if pw:
        cmd += ["-e", f"PGPASSWORD={pw}"]
    cmd += ["db", "psql", "-U", user, "-d", db, "-At", "-F", "|", "-c", sql]
    out = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", cwd=r"D:\a.Kì 1 năm 4\Hệ thống kinh doanh\TkiemViecLam")
    if out.returncode != 0:
        raise RuntimeError(out.stderr.strip())
    return [ln.split("|") for ln in out.stdout.strip().splitlines() if ln]


def call(path: str, token: str | None = None, body=None):
    req = urllib.request.Request(API + path, data=json.dumps(body).encode() if body else None, method="POST" if body else "GET")
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    return json.load(urllib.request.urlopen(req))


token = call("/auth/login", body={"email": "admin@smartcareer.vn", "password": "Demo@12345"})["access_token"]
ok = True


def check(name, cond, detail=""):
    global ok
    ok &= bool(cond)
    print(("  OK   " if cond else "  FAIL ") + name + (f"  {detail}" if detail else ""))


views = {r[0] for r in psql("select viewname from pg_views where schemaname='public'")}
check("4 view tồn tại", views == {"v_skill_supply_demand", "v_salary", "v_funnel", "v_funnel_stages"}, str(sorted(views)))

# --- phễu: v_funnel_stages (toàn thị trường) so với /bi/funnel
rows = psql("select buoc, giai_doan, sum(so_ho_so) from v_funnel_stages group by buoc, giai_doan order by buoc")
view_counts = [int(r[2]) for r in rows]
api = call("/bi/funnel", token)
api_counts = [s["count"] for s in api["stages"]]
check("phễu: view = API", view_counts == api_counts, f"{view_counts} vs {api_counts}")

conv = psql("select round(avg(hired::int)::numeric,4), percentile_cont(0.5) within group (order by ngay_den_khi_tuyen) filter (where hired) from v_funnel")[0]
# percentile_cont với filter không hợp lệ cú pháp ở mọi bản; dùng truy vấn riêng cho trung vị
median = psql("select round((percentile_cont(0.5) within group (order by ngay_den_khi_tuyen))::numeric,1) from v_funnel where hired")[0][0]
check("tỷ lệ chuyển đổi tổng: view = API", abs(float(conv[0]) - api["total_conversion"]) < 1e-4, f"{conv[0]} vs {api['total_conversion']}")
check("trung vị time-to-hire: view = API", abs(float(median) - api["median_time_to_hire_days"]) < 0.11, f"{median} vs {api['median_time_to_hire_days']}")

bands_view = {r[0]: (int(r[1]), int(r[2])) for r in psql("select nhom_diem, count(*), sum(hired::int) from v_funnel where nhom_diem is not null group by 1")}
bands_api = {b["band"].replace("–", "-"): (b["applications"], b["hired"]) for b in api["by_score_band"]}
check("hiệu quả theo nhóm điểm: view = API", bands_view == bands_api, f"{bands_view} vs {bands_api}")

# --- kỹ năng
sk_view = {r[0]: (int(r[1]), int(r[2])) for r in psql("select skill, so_ung_vien, so_tin_yeu_cau from v_skill_supply_demand")}
sk_api = {i["skill"]: (i["so_ung_vien"], i["so_tin_yeu_cau"]) for i in call("/bi/skills", token)["items"]}
check("kỹ năng (cung/cầu) 108 dòng: view = API", sk_view == sk_api, f"{len(sk_view)} vs {len(sk_api)}")

# --- lương: trung vị theo tháng và cấp bậc
sal_view = {(r[0][:7], r[1]): (round(float(r[2]), 2), int(r[3])) for r in psql(
    "select thang, level, percentile_cont(0.5) within group (order by luong_tb), count(*) from v_salary group by 1,2")}
sal_api = {(i["month"], i["level"]): (i["median_salary"], i["n"]) for i in call("/bi/salary", token)["items"]}
check("lương (trung vị tháng x cấp bậc): view = API", sal_view == sal_api, f"{len(sal_view)} vs {len(sal_api)}")

# --- RLS ở mức view: lọc theo company_id cho công ty 1
c1_view = psql("select count(*) from v_funnel where company_id = 1")[0][0]
hr1 = call("/auth/login", body={"email": "hr01@smartcareer.vn", "password": "Demo@12345"})["access_token"]
c1_api = call("/bi/funnel", hr1)["stages"][0]["count"]
check("phễu theo công ty 1: view = API", int(c1_view) == c1_api, f"{c1_view} vs {c1_api}")

# --- role chỉ đọc
rd = psql("select count(*) from v_funnel", user="bi_reader", pw="bi_reader_pw")[0][0]
check("bi_reader đọc được view", int(rd) == sum(1 for _ in range(1)) * int(rd) and int(rd) > 0, rd)
try:
    psql("select count(*) from users", user="bi_reader", pw="bi_reader_pw")
    check("bi_reader KHÔNG đọc được bảng users", False)
except RuntimeError as e:
    check("bi_reader KHÔNG đọc được bảng users", "permission denied" in str(e), str(e)[:80])

print("\nTẤT CẢ ĐẠT" if ok else "\nCÓ LỖI")

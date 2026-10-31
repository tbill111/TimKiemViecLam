"""Sinh danh mục kỹ năng, công ty và 150 tin tuyển dụng hư cấu (seed cố định = 42).

    cd backend && python -m seed.gen_data

Ghi: skills.csv, skill_aliases.csv, skill_learning_steps.csv, occupation_templates.csv, companies.csv, jobs.csv.
12 tin đầu (job-001…job-012) lấy nguyên từ frontend (legacy_jobs.json, xuất bằng scripts/export-legacy-jobs.ts).
Dữ liệu là tổng hợp, KHÔNG thu thập từ TopCV/LinkedIn.
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import random
import re
from pathlib import Path
from typing import Any

from .catalog import (
    ALIASES, BASE_SALARY, COMPANY_INDUSTRY, EXTRA_COMPANIES, LEARNING_STEPS, LOCATIONS, OCCUPATIONS, SIZES, SKILLS,
)

DATA = Path(__file__).resolve().parent / "data"
SEED = 42
N_JOBS = 150
START = dt.date(2025, 11, 1)  # tin được đăng rải đều trong 12 tháng tới 28/10/2026
END = dt.date(2026, 10, 28)

EXPERIENCE_YEARS = {"Chưa có kinh nghiệm": 0, "Dưới 1 năm": 0.5, "1-2 năm": 1, "2-3 năm": 2, "3+ năm": 3}
RESPONSIBILITIES = {
    "Frontend Development": ["Xây dựng giao diện người dùng theo thiết kế", "Viết component tái sử dụng", "Tích hợp API với đội Backend", "Tối ưu hiệu năng và khả năng hiển thị trên di động", "Tham gia review code và sprint"],
    "Backend Development": ["Thiết kế và xây dựng API REST", "Viết truy vấn và tối ưu cơ sở dữ liệu", "Viết test cho các dịch vụ", "Theo dõi lỗi và hiệu năng hệ thống", "Phối hợp với Frontend để thống nhất hợp đồng API"],
    "Data Science & Analytics": ["Làm sạch và chuẩn hoá dữ liệu", "Xây dựng báo cáo và dashboard", "Phân tích xu hướng và trình bày kết quả", "Viết truy vấn SQL cho các yêu cầu ad-hoc", "Phối hợp với bộ phận kinh doanh để xác định chỉ số"],
    "Business Analysis": ["Thu thập và phân tích yêu cầu nghiệp vụ", "Viết tài liệu user story và đặc tả", "Vẽ sơ đồ quy trình nghiệp vụ", "Làm việc với đội phát triển và kiểm thử", "Tham gia nghiệm thu với khách hàng"],
    "QA & Testing": ["Thiết kế và thực hiện test case", "Ghi nhận và theo dõi lỗi", "Kiểm thử hồi quy trước mỗi lần phát hành", "Viết kịch bản kiểm thử tự động", "Báo cáo chất lượng sản phẩm"],
    "UI/UX Design": ["Thiết kế giao diện và luồng người dùng", "Xây dựng prototype tương tác", "Thực hiện nghiên cứu và kiểm thử với người dùng", "Duy trì design system", "Bàn giao thiết kế cho đội Frontend"],
    "IT Support": ["Hỗ trợ người dùng xử lý sự cố phần cứng và phần mềm", "Quản lý tài khoản và quyền truy cập", "Cài đặt và bảo trì thiết bị mạng", "Ghi nhận và xử lý ticket", "Hướng dẫn nhân viên sử dụng công cụ nội bộ"],
    "Digital Marketing": ["Lên kế hoạch và viết nội dung cho các kênh mạng xã hội", "Theo dõi và báo cáo hiệu quả chiến dịch", "Chạy và tối ưu quảng cáo", "Tối ưu nội dung cho công cụ tìm kiếm", "Phối hợp với đội thiết kế"],
    "Software Engineering": ["Phát triển tính năng mới cho sản phẩm", "Viết test và tài liệu kỹ thuật", "Tham gia thiết kế kiến trúc và review code", "Triển khai và theo dõi hệ thống", "Phối hợp trong quy trình Agile"],
    "Business Operations": ["Theo dõi và cải tiến quy trình vận hành", "Tổng hợp số liệu và lập báo cáo định kỳ", "Phối hợp giữa các bộ phận", "Hỗ trợ đối tác và khách hàng", "Soạn tài liệu quy trình"],
}
LEVEL_MIN_YEARS = {"intern": [0], "fresher": [0, 0.5], "junior": [1, 1], "middle": [2, 3], "senior": [3, 3]}


def write_csv(path: Path, header: list[str], rows: list[list[Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def parse_salary(text: str) -> tuple[float, float]:
    """'3,000,000 – 5,000,000 VNĐ/tháng' → (3.0, 5.0) triệu VNĐ."""
    nums = [int(n.replace(",", "")) / 1_000_000 for n in re.findall(r"\d[\d,]*", text)]
    return nums[0], nums[1]


def legacy_rows(legacy: dict) -> tuple[list[list[Any]], dict[str, dict[str, str]]]:
    rows, companies = [], {}
    for j in legacy["jobs"]:
        wt = j["workType"]
        job_type = {"Thực tập": "internship", "Bán thời gian": "part_time"}.get(wt, "full_time")
        work_mode = "remote" if wt == "Remote" else "onsite"
        level = "intern" if wt == "Thực tập" else "fresher"
        lo, hi = parse_salary(j["salary"])
        required = [s for s in j["requiredSkills"] if " hoặc " not in s]
        preferred = list(j["preferredSkills"])
        for s in j["requiredSkills"]:  # 'React hoặc Node.js' → hai kỹ năng ưu tiên (DB chỉ lưu kỹ năng đơn)
            if " hoặc " in s:
                preferred = [x.strip() for x in s.split(" hoặc ")] + preferred
        posted = dt.date.fromisoformat(j["postedAt"][:10])
        rows.append([
            j["id"], j["company"], j["title"], j["category"], level, job_type, work_mode, j["location"], lo, hi,
            EXPERIENCE_YEARS[j["experienceLevel"]], 2 if j["category"] == "IT Support" else 3, posted.isoformat(),
            (posted + dt.timedelta(days=45)).isoformat(), j["description"], "|".join(j["responsibilities"]),
            "|".join(dict.fromkeys(required)), "|".join(dict.fromkeys(preferred)),
        ])
        companies.setdefault(j["company"], {"industry": j.get("companyIndustry", ""), "size": j.get("companySize", ""), "location": j["location"]})
    return rows, companies


def build_companies(rng: random.Random, legacy_companies: dict[str, dict[str, str]]) -> list[list[str]]:
    rows = [[n, c["industry"], c["size"], c["location"]] for n, c in legacy_companies.items()]
    cats = list(OCCUPATIONS)
    for i, name in enumerate(EXTRA_COMPANIES):
        loc = rng.choices(["Hà Nội", "Hồ Chí Minh", "Đà Nẵng", "Hải Phòng", "Cần Thơ"], weights=[35, 35, 14, 8, 8])[0]
        rows.append([name, COMPANY_INDUSTRY[cats[i % len(cats)]], rng.choice(SIZES), loc])
    return rows


def months_between(a: dt.date, b: dt.date) -> int:
    return (b.year - a.year) * 12 + b.month - a.month


def generated_job(i: int, rng: random.Random, companies: list[list[str]], day: dt.date) -> list[Any]:
    cat = list(OCCUPATIONS)[i % len(OCCUPATIONS)]
    occ = OCCUPATIONS[cat]
    level = rng.choices(["intern", "fresher", "junior", "middle", "senior"], weights=[26, 30, 24, 15, 5])[0]
    job_type = "internship" if level == "intern" else ("part_time" if rng.random() < 0.06 else "full_time")
    work_mode = rng.choices(["onsite", "hybrid", "remote"], weights=[58, 27, 15])[0]
    company = rng.choice(companies)
    location = "Remote" if work_mode == "remote" else rng.choices(["Hà Nội", "Hồ Chí Minh", "Đà Nẵng", "Hải Phòng", "Cần Thơ"], weights=[35, 35, 14, 8, 8])[0]
    title = f"{rng.choice(occ['titles'])}{' Intern' if level == 'intern' else ''}{' (Senior)' if level == 'senior' else ''}"
    trend = 1 + 0.012 * months_between(START, day)  # lương tin tăng nhẹ theo thời gian
    mid = BASE_SALARY[level] * trend * rng.uniform(0.9, 1.12)
    lo, hi = (round(mid * 0.85, 1), round(mid * 1.15, 1)) if rng.random() > 0.08 else ("", "")
    n_core = rng.choice([3, 4, 5])
    core = occ["core"][:max(3, min(n_core, len(occ["core"])))]
    pref = rng.sample(occ["optional"], k=rng.choice([2, 3, 4]))
    description = (f"{company[0]} ({company[1]}) tuyển {title} làm việc tại {location}. Bạn sẽ tham gia các dự án thực tế trong lĩnh vực {cat}, "
                   f"được hướng dẫn bởi đội ngũ có kinh nghiệm và cơ hội phát triển lâu dài.")
    return [
        f"job-{i + 1:03d}", company[0], title, cat, level, job_type, work_mode, location, lo, hi,
        rng.choice(LEVEL_MIN_YEARS[level]), 4 if rng.random() < 0.03 else 3, day.isoformat(), (day + dt.timedelta(days=rng.choice([30, 45, 60]))).isoformat(),
        description, "|".join(rng.sample(RESPONSIBILITIES[cat], k=rng.choice([3, 4, 5]))), "|".join(core), "|".join(pref),
    ]


JOBS_HEADER = ["external_id", "company_name", "title", "category", "level", "job_type", "work_mode", "location", "salary_min", "salary_max",
               "min_years_exp", "min_education", "posted_at", "deadline", "description", "responsibilities", "required_skills", "preferred_skills"]


def main(out: Path = DATA) -> None:
    rng = random.Random(SEED)
    legacy = json.loads((DATA / "legacy_jobs.json").read_text(encoding="utf-8"))
    legacy_job_rows, legacy_companies = legacy_rows(legacy)
    companies = build_companies(rng, legacy_companies)
    n_new = N_JOBS - len(legacy_job_rows)
    span = (END - START).days
    days = sorted(START + dt.timedelta(days=round(k * span / (n_new - 1))) for k in range(n_new))  # rải đều 12 tháng
    seen = {(r[2], r[1]) for r in legacy_job_rows}
    new_rows: list[list[Any]] = []
    for k in range(n_new):
        while True:  # không để trùng (tên vị trí, công ty) – cùng quy tắc kiểm tra chất lượng ở trang ETL
            row = generated_job(len(legacy_job_rows) + k, rng, companies, days[k])
            if (row[2], row[1]) not in seen:
                seen.add((row[2], row[1]))
                break
        new_rows.append(row)
    rows = legacy_job_rows + new_rows

    write_csv(out / "skills.csv", ["name", "category"], [[n, c] for n, c in SKILLS])
    write_csv(out / "skill_aliases.csv", ["alias", "skill_name"], [[a, n] for n, al in ALIASES.items() for a in al])
    write_csv(out / "skill_learning_steps.csv", ["skill_name", "steps"], [[n, "|".join(s)] for n, s in LEARNING_STEPS.items()])
    write_csv(out / "occupation_templates.csv", ["occupation", "core_skills", "optional_skills"],
              [[o, "|".join(v["core"]), "|".join(v["optional"])] for o, v in OCCUPATIONS.items()])
    write_csv(out / "companies.csv", ["name", "industry", "size_range", "location"], companies)
    write_csv(out / "jobs.csv", JOBS_HEADER, rows)
    write_csv(out / "locations.csv", ["name", "region"], [[n, r] for n, r in LOCATIONS])
    print(f"skills={len(SKILLS)} aliases={sum(len(a) for a in ALIASES.values())} companies={len(companies)} jobs={len(rows)}")


if __name__ == "__main__":
    main()

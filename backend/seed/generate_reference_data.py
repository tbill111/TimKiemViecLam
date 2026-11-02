"""Complete deterministic backend demo CSVs from the 12 frontend fixtures.

Keep jobs.csv as the three-row AI evaluation fixture; the full backend job
catalog is written to jobs_seed.csv. Run after export_frontend_jobs.mjs.
"""
from __future__ import annotations

import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "data"
random.seed(42)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def skill_data() -> list[dict[str, str]]:
    json_path = Path(__file__).resolve().parents[1] / "app" / "ai" / "default_skills.json"
    defaults = json.loads(json_path.read_text(encoding="utf-8"))["skills"]
    category_by_name = {row["name"]: row.get("category", "Khác") for row in defaults}
    rows = {row["name"].strip(): row.get("category", "Khác") for row in read_csv(ROOT / "skills.csv")}
    rows.update(category_by_name)
    extras = {
        "TypeScript nâng cao": "Frontend", "Quản lý dự án": "Kỹ năng mềm",
        "Thiết kế API": "Backend", "Bảo mật ứng dụng": "Backend", "Phân tích dữ liệu": "Dữ liệu",
        "Responsive Design": "Frontend",
    }
    rows.update({name: category for name, category in extras.items() if name not in rows})
    return [{"name": name, "category": category} for name, category in sorted(rows.items())]


def companies_data(legacy: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    for row in read_csv(ROOT / "companies.csv"):
        rows[row["name"]] = row
    for job in legacy:
        rows.setdefault(job["company_name"], {"name": job["company_name"], "industry": "Phần mềm & Công nghệ", "size_range": "50–200 nhân viên", "location": job["location"]})
    cities = ["Hà Nội", "Hồ Chí Minh", "Đà Nẵng", "Remote"]
    industries = ["Phần mềm & Công nghệ", "Tài chính số", "Phân tích dữ liệu", "Thương mại điện tử", "Thiết kế sản phẩm"]
    while len(rows) < 30:
        number = len(rows) + 1
        name = f"SmartCareer Demo Company {number:02d}"
        rows[name] = {"name": name, "industry": industries[(number - 1) % len(industries)], "size_range": ["10–50 nhân viên", "50–200 nhân viên", "200–500 nhân viên"][number % 3], "location": cities[(number - 1) % len(cities)]}
    return list(rows.values())[:30]


def aliases_data(skills: list[dict[str, str]]) -> list[dict[str, str]]:
    result: dict[str, str] = {}
    for row in read_csv(ROOT / "skill_aliases.csv"):
        result[row["alias"].strip()] = row["skill_name"].strip()
    json_path = Path(__file__).resolve().parents[1] / "app" / "ai" / "default_skills.json"
    defaults = json.loads(json_path.read_text(encoding="utf-8"))["aliases"]
    canonical = {row["name"].casefold() for row in skills}
    for skill, aliases in defaults.items():
        for alias in aliases:
            if alias.casefold() not in canonical:
                result.setdefault(alias, skill)
    for row in skills:
        name = row["name"]
        variants = [name.lower().replace(" ", "-"), name.lower().replace(" ", ""), name.replace(".", ""), name.replace(" ", "_")]
        if name.endswith(" cơ bản"):
            variants.append(name.removesuffix(" cơ bản"))
        if "." in name:
            variants.extend([name.replace(".", ""), name.replace(".", " ")])
        for alias in variants:
            if alias.casefold() != name.casefold() and alias.casefold() not in canonical:
                result.setdefault(alias, name)
    return [{"alias": alias, "skill_name": skill} for alias, skill in sorted(result.items())[:180]]


def jobs_data(legacy: list[dict[str, str]], companies: list[dict[str, str]]) -> list[dict[str, str]]:
    fields = ["external_id", "company_name", "title", "category", "level", "job_type", "work_mode", "location", "salary_min", "salary_max", "min_years_exp", "min_education", "posted_at", "deadline", "description", "responsibilities", "required_skills", "preferred_skills"]
    rows = {row["external_id"]: row for row in read_csv(ROOT / "jobs_seed.csv")}
    rows.update({row["external_id"]: row for row in legacy})
    if not legacy:
        legacy = list(rows.values())
    levels = [("intern", 0, "internship"), ("fresher", 0, "full_time"), ("junior", 1, "full_time"), ("middle", 2, "full_time"), ("senior", 3, "full_time")]
    cities = ["Hà Nội", "Hồ Chí Minh", "Đà Nẵng", "Remote"]
    while len(rows) < 150:
        number = len(rows) + 1
        base = legacy[(number - 1) % len(legacy)]
        level, years, job_type = levels[(number - 1) % len(levels)]
        company = companies[(number * 7) % len(companies)]
        low = round((2.5 if level == "intern" else 7 + years * 3) + (number % 4) * 0.5, 1)
        high = low + (2.0 if level == "intern" else 4.0 + (number % 3))
        month = (number - 1) % 12 + 1
        posted = date(2025 if month > 10 else 2026, month, min(25, 1 + number % 25))
        deadline = posted + timedelta(days=45)
        external_id = f"sim-job-{number:03d}"
        rows[external_id] = {
            "external_id": external_id,
            "company_name": company["name"],
            "title": f"{base['title']} – {level.title()}",
            "category": base["category"], "level": level, "job_type": job_type,
            "work_mode": "remote" if cities[number % 4] == "Remote" else ["onsite", "hybrid"][number % 2],
            "location": cities[number % 4], "salary_min": str(low), "salary_max": str(high),
            "min_years_exp": str(years), "min_education": str((number % 4) + 1),
            "posted_at": posted.isoformat(), "deadline": (posted + timedelta(days=400)).isoformat(),
            "description": f"Tin tuyển dụng mô phỏng cho {base['category']}, dùng để minh họa dữ liệu tìm việc SmartCareer.",
            "responsibilities": base["responsibilities"], "required_skills": base["required_skills"],
            "preferred_skills": base["preferred_skills"],
        }
    return [{field: row.get(field, "") for field in fields} for row in list(rows.values())[:150]]


def main() -> None:
    legacy = read_csv(ROOT / "frontend_jobs.csv")
    skills = skill_data()
    companies = companies_data(legacy)
    jobs = jobs_data(legacy, companies)
    aliases = aliases_data(skills)
    write_csv(ROOT / "skills.csv", ["name", "category"], skills)
    write_csv(ROOT / "skill_aliases.csv", ["alias", "skill_name"], aliases)
    write_csv(ROOT / "companies.csv", ["name", "industry", "size_range", "location"], companies)
    write_csv(ROOT / "jobs_seed.csv", ["external_id", "company_name", "title", "category", "level", "job_type", "work_mode", "location", "salary_min", "salary_max", "min_years_exp", "min_education", "posted_at", "deadline", "description", "responsibilities", "required_skills", "preferred_skills"], jobs)
    templates: dict[str, dict[str, list[str]]] = {}
    for job in jobs:
        group = job["category"]
        entry = templates.setdefault(group, {"core": [], "optional": []})
        entry["core"].extend(job["required_skills"].split("|") if job["required_skills"] else [])
        entry["optional"].extend(job["preferred_skills"].split("|") if job["preferred_skills"] else [])
    occupation_rows = []
    for occupation, values in sorted(templates.items()):
        core = list(dict.fromkeys(values["core"]))[:10]
        optional = [skill for skill in dict.fromkeys(values["optional"]) if skill not in core][:12]
        occupation_rows.append({"occupation": occupation, "core_skills": "|".join(core), "optional_skills": "|".join(optional)})
    write_csv(ROOT / "occupation_templates.csv", ["occupation", "core_skills", "optional_skills"], occupation_rows)
    print(f"Generated {len(skills)} skills, {len(aliases)} aliases, {len(companies)} companies, {len(jobs)} jobs and {len(occupation_rows)} occupation templates (seed=42).")


if __name__ == "__main__":
    main()

"""Generate 300 deterministic simulated candidate profiles and export the AI CSV contract."""
from __future__ import annotations

import csv
import json
import random
from pathlib import Path

from faker import Faker

DATA_DIR = Path(__file__).resolve().parent / "data"
OUT = DATA_DIR / "candidates_generated.csv"
LOCATIONS = ["Hà Nội", "Hồ Chí Minh", "Đà Nẵng", "Remote"]
WORK_TYPES = ["Toàn thời gian", "Bán thời gian", "Thực tập", "Remote"]


def _read(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def generate_profiles(count: int = 300) -> list[dict]:
    rng = random.Random(42)
    fake = Faker("vi_VN")
    fake.seed_instance(42)
    templates = _read(DATA_DIR / "occupation_templates.csv")
    all_skills = [row["name"] for row in _read(DATA_DIR / "skills.csv")]
    if not templates:
        raise RuntimeError("occupation_templates.csv is empty; run generate_reference_data.py first")
    profiles = []
    for index in range(count):
        if index == 0:
            occupation = "Frontend Development"
            skills = ["HTML", "CSS", "JavaScript", "React", "Git", "SQL", "Python", "Figma", "Responsive Design"]
            locations, work_types = ["Hà Nội", "Remote"], ["Thực tập", "Remote"]
            profile = {
                "fullName": "Giang Thanh Tùng", "university": "Trường Đại học Thủy lợi", "major": "Công nghệ Thông tin",
                "year": "Năm 4 (2022–2026)", "email": "thanhtung.demo@smartcareer.vn", "phone": "09000000001",
                "githubUrl": "", "linkedinUrl": "", "careerGoal": "Mong muốn trở thành Frontend Developer tại một công ty công nghệ năng động, nơi có thể dùng React và TypeScript xây dựng sản phẩm có ích; định hướng Full-stack Developer hoặc Tech Lead.",
                "skills": skills, "preferredLocations": locations, "preferredWorkTypes": work_types,
                "languages": ["Tiếng Việt (Bản ngữ)", "Tiếng Anh (B2 – IELTS 6.5)"],
                "projects": [
                    {"id": "proj-001", "name": "SmartTask – Quản lý Công việc Nhóm", "description": "Ứng dụng web quản lý công việc nhóm với board Kanban và theo dõi tiến độ.", "technologies": ["React", "Node.js", "MongoDB", "Socket.IO", "Tailwind CSS"], "url": "https://github.com/minhanh/smarttask"},
                    {"id": "proj-002", "name": "EcoMarket – Sàn Thương mại Điện tử Xanh", "description": "Website thương mại điện tử với tìm kiếm nâng cao và đánh giá sản phẩm.", "technologies": ["React", "Django", "PostgreSQL", "Redux", "Bootstrap"], "url": "https://github.com/minhanh/ecomarket"},
                    {"id": "proj-003", "name": "StudentHub – Mạng xã hội Học thuật", "description": "Nền tảng chia sẻ tài liệu và thảo luận học thuật.", "technologies": ["HTML", "CSS", "JavaScript", "PHP", "MySQL"]},
                ],
                "experience": [
                    {"id": "exp-001", "position": "Frontend Developer Part-time", "company": "Studio404 Design Agency", "duration": "Tháng 6/2025 – Tháng 9/2025 (4 tháng)", "description": "Xây dựng landing page responsive bằng React và Tailwind CSS."},
                    {"id": "exp-002", "position": "Trưởng nhóm Kỹ thuật – CLB Tin học", "company": "Câu lạc bộ Tin học – Trường Đại học Thủy lợi", "duration": "Tháng 9/2024 – Tháng 6/2025 (9 tháng)", "description": "Dẫn dắt 8 sinh viên tổ chức workshop và duy trì website câu lạc bộ."},
                ],
                "certificates": [
                    {"id": "cert-001", "name": "Meta Front-End Developer Professional Certificate", "issuer": "Meta / Coursera", "year": "2025"},
                    {"id": "cert-002", "name": "Google Data Analytics Certificate", "issuer": "Google / Coursera", "year": "2024"},
                    {"id": "cert-003", "name": "IELTS Academic 6.5", "issuer": "British Council", "year": "2024"},
                ], "profileCompletion": 82,
            }
            years_exp, education_level = 1.0, 3
            text = "Kỹ năng\nReact, TypeScript, HTML, CSS, Git\nKinh nghiệm\nFrontend Developer part time; phát triển giao diện React.\nHọc vấn\nĐại học Thủy lợi, Công nghệ Thông tin"
        else:
            template = templates[(index - 1) % len(templates)]
            occupation = template["occupation"]
            core = [s for s in template["core_skills"].split("|") if s]
            optional = [s for s in template["optional_skills"].split("|") if s]
            if not core:
                core = all_skills[:8]
            pool = list(dict.fromkeys(core + optional + all_skills))
            skills = rng.sample(core, min(len(core), rng.randint(3, 6))) if core else []
            remaining = [skill for skill in pool if skill not in skills]
            skills += rng.sample(remaining, min(len(remaining), max(0, rng.randint(5, 12) - len(skills))))
            skills = skills[:12]
            years_exp = round(rng.choice([0, 0.3, 0.5, 1, 1.5, 2, 3, 4, 5]), 1)
            education_level = rng.choices([0, 1, 2, 3, 4], weights=[5, 5, 15, 65, 10])[0]
            locations = rng.sample(LOCATIONS, rng.choice([1, 1, 2]))
            work_types = rng.sample(WORK_TYPES, rng.choice([1, 2]))
            full_name = fake.name()
            profile = {
                "fullName": full_name, "university": rng.choice(["Đại học Bách khoa", "Đại học Quốc gia", "Đại học Kinh tế", "Cao đẳng Công nghệ"]),
                "major": occupation, "year": rng.choice(["Năm 2", "Năm 3", "Năm 4", "Đã tốt nghiệp"]),
                "email": f"candidate{index + 1:03d}@smartcareer.vn", "phone": f"09{rng.randrange(10**8):08d}",
                "githubUrl": "", "linkedinUrl": "", "careerGoal": f"Tìm cơ hội phát triển trong lĩnh vực {occupation}.",
                "skills": skills, "preferredLocations": locations, "preferredWorkTypes": work_types,
                "languages": ["Tiếng Việt"], "projects": [], "experience": [], "certificates": [], "profileCompletion": rng.randint(60, 100),
            }
            text = f"Mục tiêu\n{profile['careerGoal']}\nKỹ năng\n{' | '.join(skills)}\nKinh nghiệm\n{years_exp} năm kinh nghiệm trong nhóm nghề {occupation}.\nHọc vấn\n{profile['university']}"
        profiles.append({
            "candidate_id": "cand-demo-001" if index == 0 else f"cand-gen-{index:04d}",
            "occupation": occupation, "skills": skills, "years_exp": years_exp, "education_level": education_level,
            "locations": locations, "work_types": work_types, "expected_salary_min": round(4 + years_exp * 2, 1),
            "expected_salary_max": round(7 + years_exp * 3, 1), "text": text, "profile_json": profile,
            "cv_file": None,
        })
    # Attach only files handed over in a real manifest; never claim missing CVs exist.
    candidates = [Path(__file__).resolve().parent / "cv_files" / "cv_manifest.csv", Path(__file__).resolve().parent / "cv_manifest.csv", DATA_DIR / "cv_manifest.csv"]
    manifest_path = next((path for path in candidates if path.exists()), candidates[0])
    if manifest_path.exists():
        manifest = _read(manifest_path)
        files = [row.get("cv_file") or row.get("filename") for row in manifest if row.get("cv_file") or row.get("filename")]
        for profile, filename in zip(profiles[:50], files[:50]):
            profile["cv_file"] = filename
    return profiles


def export_csv(profiles: list[dict], path: Path = OUT) -> None:
    fields = ["candidate_id", "occupation", "skills", "years_exp", "education_level", "locations", "work_types", "expected_salary_min", "expected_salary_max", "text"]
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in profiles:
            writer.writerow({
                "candidate_id": row["candidate_id"], "occupation": row["occupation"], "skills": "|".join(row["skills"]),
                "years_exp": row["years_exp"], "education_level": row["education_level"], "locations": "|".join(row["locations"]),
                "work_types": "|".join(row["work_types"]), "expected_salary_min": row["expected_salary_min"],
                "expected_salary_max": row["expected_salary_max"], "text": row["text"],
            })


def main() -> None:
    profiles = generate_profiles()
    export_csv(profiles)
    print(f"Generated {len(profiles)} candidates (seed=42) at {OUT}")


if __name__ == "__main__":
    main()

"""Sinh 300 hồ sơ ứng viên hư cấu theo mẫu nghề (seed cố định = 42).

    cd backend && python -m seed.gen_candidates

Ghi seed/data/candidates_generated.csv. Tên, email, số điện thoại đều là giả.
Mỗi ứng viên có "độ mạnh" ngẫu nhiên nên điểm khớp phân bố đủ rộng (không phải ai cũng khớp mọi tin).
"""
from __future__ import annotations

import csv
import random
import unicodedata
from pathlib import Path
from typing import Any

from faker import Faker

from .catalog import BASE_SALARY, OCCUPATIONS, SKILLS

DATA = Path(__file__).resolve().parent / "data"
SEED = 42
N = 300

UNIVERSITIES = [
    "Đại học Thủy lợi", "Đại học Bách khoa Hà Nội", "Đại học Công nghệ – ĐHQGHN", "Đại học Kinh tế Quốc dân",
    "Học viện Công nghệ Bưu chính Viễn thông", "Đại học Khoa học Tự nhiên TP.HCM", "Đại học Bách khoa TP.HCM",
    "Đại học FPT", "Đại học Duy Tân", "Đại học Cần Thơ", "Đại học Mở Hà Nội", "Đại học Sư phạm Kỹ thuật TP.HCM",
]
COMMON_SKILLS = ["Git", "Giao tiếp", "Làm việc nhóm", "Tiếng Anh giao tiếp", "Thuyết trình", "Tư duy logic"]
YEARS = [(0, 0.50), (0.5, 0.15), (1, 0.15), (2, 0.12), (3, 0.08)]
CITIES = ["Hà Nội", "Hồ Chí Minh", "Đà Nẵng", "Hải Phòng", "Cần Thơ"]
HEADER = ["candidate_id", "occupation", "skills", "years_exp", "education_level", "locations", "work_types", "expected_salary_min",
          "expected_salary_max", "text", "full_name", "university", "year", "major", "phone", "career_goal"]
_SKILL_NAMES = {n for n, _ in SKILLS}


def ascii_slug(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", text.lower()) if c.isalnum() and ord(c) < 128)


def level_for(years: float) -> str:
    return "intern" if years == 0 else "fresher" if years < 1 else "junior" if years < 2 else "middle"


def generate(n: int = N, seed: int = SEED) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    fake = Faker("vi_VN")
    fake.seed_instance(seed)
    cats = list(OCCUPATIONS)
    rows: list[dict[str, Any]] = []
    for i in range(n):
        cat = cats[i % len(cats)] if i < len(cats) * (n // len(cats)) else rng.choice(cats)
        occ = OCCUPATIONS[cat]
        strength = rng.betavariate(2, 2)
        skills = [s for s in occ["core"] if rng.random() < 0.35 + 0.6 * strength]
        skills += [s for s in occ["optional"] if rng.random() < 0.08 + 0.4 * strength]
        skills += [s for s in COMMON_SKILLS if s not in skills and rng.random() < 0.18]
        while len(skills) < 3:  # mọi hồ sơ có ít nhất 3 kỹ năng
            extra = rng.choice(occ["core"] + occ["optional"])
            if extra not in skills:
                skills.append(extra)
        assert set(skills) <= _SKILL_NAMES
        years = rng.choices([y for y, _ in YEARS], weights=[w for _, w in YEARS])[0]
        edu = rng.choices([3, 2, 4], weights=[85, 9, 6])[0]
        locations = rng.sample(CITIES, k=rng.choice([1, 1, 2]))
        if rng.random() < 0.2:
            locations.append("Remote")
        pool = ["Thực tập"] * 6 + ["Toàn thời gian"] * 5 + ["Bán thời gian"] + ["Remote"] * 2
        target = rng.choice([1, 2])
        work_types: list[str] = []
        while len(work_types) < target:
            w = rng.choice(pool)
            if w not in work_types:
                work_types.append(w)
        if years == 0 and "Thực tập" not in work_types and rng.random() < 0.7:
            work_types[0] = "Thực tập"
        base = BASE_SALARY[level_for(years)]
        sal = (round(base * 0.8, 1), round(base * 1.2, 1)) if rng.random() < 0.55 else ("", "")
        # Họ + đệm + tên cùng giới (Faker.name() có thể sinh tiền tố xưng hô như "Bác", "Ông", "Chị")
        female = rng.random() < 0.5
        middle = "Thị" if female else "Văn"
        if rng.random() < 0.45:  # đệm khác; tránh "Thị" cho nam và "Văn" cho nữ
            while (m := fake.middle_name()) in ("Thị", "Văn"):
                pass
            middle = m
        first = fake.first_name_female() if female else fake.first_name_male()
        last = fake.last_name_female() if female else fake.last_name_male()
        name = f"{last} {middle} {first}"
        title = rng.choice(occ["titles"])
        goal = f"Mong muốn trở thành {title} và phát triển chuyên môn trong lĩnh vực {cat}."
        rows.append({
            "candidate_id": f"cand-{i + 1:04d}", "occupation": cat, "skills": "|".join(skills), "years_exp": years,
            "education_level": edu, "locations": "|".join(locations), "work_types": "|".join(work_types),
            "expected_salary_min": sal[0], "expected_salary_max": sal[1],
            "text": f"{goal} Kỹ năng: {', '.join(skills)}.", "full_name": name, "university": rng.choice(UNIVERSITIES),
            "year": rng.choice(["Năm 3", "Năm 4", "Năm 4", "Đã tốt nghiệp"]), "major": occ["major"],
            "phone": "09" + "".join(str(rng.randint(0, 9)) for _ in range(8)), "career_goal": goal,
        })
    return rows


def write(rows: list[dict[str, Any]], path: Path = DATA / "candidates_generated.csv") -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=HEADER)
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    rows = generate()
    write(rows)
    print(f"Đã ghi {len(rows)} ứng viên vào {DATA / 'candidates_generated.csv'}")


if __name__ == "__main__":
    main()

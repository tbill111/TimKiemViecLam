"""Dữ liệu tổng hợp nhỏ để kiểm tra luồng đánh giá/huấn luyện chạy được từ đầu đến cuối.

Số liệu từ dữ liệu này KHÔNG phản ánh chất lượng mô hình; chỉ kiểm tra mã và định dạng file.
"""
from __future__ import annotations

import csv
import random
from pathlib import Path

CATS = {
    "Frontend Development": (["HTML", "CSS", "JavaScript", "React", "Git"], ["TypeScript", "Tailwind CSS"]),
    "Data Science & Analytics": (["SQL", "Python", "Excel", "Thống kê cơ bản"], ["Power BI", "Pandas"]),
    "QA & Testing": (["Kiểm thử phần mềm", "SQL", "Git"], ["Postman", "Agile/Scrum"]),
    "Backend Development": (["Node.js", "SQL", "REST API", "Git"], ["Docker", "PostgreSQL"]),
}


def _w(path: Path, header: list[str], rows: list[list]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def build(root: Path, n_cand: int = 24, n_jobs: int = 24, seed: int = 0) -> dict[str, Path]:
    rng = random.Random(seed)
    cats = list(CATS)
    jobs = []
    for i in range(n_jobs):
        cat = cats[i % len(cats)]
        req, pref = CATS[cat]
        jobs.append([
            f"job-{i + 1:03d}", "Công ty Mẫu", f"Vị trí {cat} {i}", cat, "intern", "internship", "onsite", "Hà Nội", 3, 5, 0, 3,
            "2026-10-01", "2026-12-01", f"Tuyển dụng {cat}", "Việc 1|Việc 2", "|".join(req), "|".join(pref),
        ])
    _w(root / "jobs.csv", ["external_id", "company_name", "title", "category", "level", "job_type", "work_mode", "location",
                           "salary_min", "salary_max", "min_years_exp", "min_education", "posted_at", "deadline",
                           "description", "responsibilities", "required_skills", "preferred_skills"], jobs)
    cands, pairs_a, pairs_b = [], [], []
    for i in range(n_cand):
        cat = cats[i % len(cats)]
        req, pref = CATS[cat]
        have = req[: rng.randint(2, len(req))] + pref[: rng.randint(0, len(pref))]
        cands.append([f"cand-{i + 1:04d}", cat, "|".join(have), rng.choice([0, 0.5, 1]), 3, "Hà Nội", "Thực tập", "", "", f"Sinh viên {cat} " + " ".join(have)])
        for j in rng.sample(range(n_jobs), 10):
            job_cat = cats[j % len(cats)]
            overlap = len(set(have) & set(CATS[job_cat][0])) / len(CATS[job_cat][0])
            label = 3 if overlap >= 0.9 else 2 if overlap >= 0.5 else 1 if overlap > 0 else 0
            pairs_a.append([f"cand-{i + 1:04d}", f"job-{j + 1:03d}", label])
            pairs_b.append([f"cand-{i + 1:04d}", f"job-{j + 1:03d}", max(0, min(3, label + rng.choice([0, 0, 0, 1, -1])))])
    _w(root / "candidates_generated.csv", ["candidate_id", "occupation", "skills", "years_exp", "education_level", "locations",
                                           "work_types", "expected_salary_min", "expected_salary_max", "text"], cands)
    _w(root / "labels_pairs_a.csv", ["candidate_id", "job_id", "label"], pairs_a)
    _w(root / "labels_pairs_b.csv", ["candidate_id", "job_id", "label"], pairs_b)
    # 6 CV dạng txt có nhãn kỹ năng
    cv_rows = []
    for k in range(6):
        cat = cats[k % len(cats)]
        req, pref = CATS[cat]
        text = f"Nguyễn Văn {k}\nKỹ năng\n{', '.join(req)}\nKinh nghiệm\nIntern 06/2024 - 08/2024\nHọc vấn\nĐại học Thủy lợi\n"
        (root / "cvs").mkdir(exist_ok=True)
        (root / "cvs" / f"cv_{k:03d}.txt").write_text(text, encoding="utf-8")
        cv_rows.append([f"cv_{k:03d}.txt", "|".join(req), 0.2])
    _w(root / "labels_cv_skills.csv", ["cv_file", "skills", "years_exp"], cv_rows)
    return {"root": root, "jobs": root / "jobs.csv", "cands": root / "candidates_generated.csv", "a": root / "labels_pairs_a.csv",
            "b": root / "labels_pairs_b.csv", "cv_dir": root / "cvs", "cv_labels": root / "labels_cv_skills.csv"}

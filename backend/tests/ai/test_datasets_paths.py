from app.ai.datasets import default_jobs_path

HEADER = "external_id,company_name,title,category,level,job_type,work_mode,location,salary_min,salary_max,min_years_exp,min_education,posted_at,deadline,description,responsibilities,required_skills,preferred_skills\n"


def _write(path, rows):
    path.write_text(HEADER + "".join(f"job-{i},C,T,Frontend Development,intern,internship,onsite,Hà Nội,,,0,0,,,d,r,React,Git\n" for i in range(rows)), encoding="utf-8")


def test_default_jobs_path_prefers_full_seed_file_over_small_template(tmp_path):
    _write(tmp_path / "jobs.csv", 3)
    assert default_jobs_path(tmp_path).name == "jobs.csv"  # chưa có jobs_seed.csv
    _write(tmp_path / "jobs_seed.csv", 5)
    assert default_jobs_path(tmp_path).name == "jobs.csv"  # jobs_seed.csv quá ít dòng: coi là mẫu
    _write(tmp_path / "jobs_seed.csv", 150)
    assert default_jobs_path(tmp_path).name == "jobs_seed.csv"

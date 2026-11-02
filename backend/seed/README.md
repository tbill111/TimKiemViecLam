# Seed data and CSV contracts

All CSV files use UTF-8, comma-delimited fields, and `|` inside cells for lists. Names are fictional and the additional company/job/application records are generated demo data, not scraped labor-market data.

## Reference data

`data/skills.csv`, `skill_aliases.csv`, `companies.csv`, `jobs_seed.csv`, `occupation_templates.csv`, and `skill_learning_steps.csv` are checked in. `jobs.csv` remains the original three-row AI evaluation fixture; the backend seed catalog lives in `jobs_seed.csv` so the AI evaluation contract stays stable. That catalog includes all 12 frontend jobs and deterministic simulated records (seed 42). `frontend_jobs.csv` preserves the original 12 frontend fixtures. The complete reference data meets the project minima: 80 skills, 150 aliases, 30 companies, 150 jobs, and 8 occupation templates.

To rebuild the frontend export and deterministic simulated rows:

```bash
# repository root, after npm ci
node backend/seed/export_frontend_jobs.mjs
python backend/seed/generate_reference_data.py
```

## File formats

| File | Columns |
|---|---|
| `skills.csv` | `name,category` |
| `skill_aliases.csv` | `alias,skill_name` |
| `occupation_templates.csv` | `occupation,core_skills,optional_skills` |
| `companies.csv` | `name,industry,size_range,location` |
| `skill_learning_steps.csv` | `skill_name,steps` |
| `jobs.csv` | Original three-row AI evaluation fixture; same columns as `jobs_seed.csv` |
| `jobs_seed.csv` | `external_id,company_name,title,category,level,job_type,work_mode,location,salary_min,salary_max,min_years_exp,min_education,posted_at,deadline,description,responsibilities,required_skills,preferred_skills` |
| `candidates_generated.csv` | `candidate_id,occupation,skills,years_exp,education_level,locations,work_types,expected_salary_min,expected_salary_max,text` |
| `labels/labels_pairs_<name>.csv` | `candidate_id,job_id,label` |
| `labels/labels_cv_skills.csv` | `cv_file,skills` (optional `years_exp`) |

Salary values are in million VND per month. `min_education` and `education_level` use 0–4. Candidate work types are frontend Vietnamese labels. Candidate and job IDs in label files are external IDs. Job skills are canonical single skill names; the legacy label `React hoặc Node.js` is split into two preferred skills.

`gen_candidates.py` uses `Faker('vi_VN')`, deterministic random seed 42, and the occupation templates. The first stable candidate row represents the demo profile `Giang Thanh Tùng`; the other 299 candidates are fictional. It attaches CV filenames only when a real `cv_manifest.csv` and corresponding files are present. This checkout has no CV handoff, so the loader does not invent CV attachments.

`gen_applications.py` creates approximately 1,200 application rows with status history. Funnel choices are random and independent of `match_score`; they demonstrate BI calculations and are not evidence of model quality. `match_score` is computed with `score_pair('m3', ...)`.

Run `python -m seed.load_seed --reset` from `backend/`. Seed writes are idempotent, use one transaction protected by `pg_advisory_xact_lock`, and `--reset` drops/recreates the BI views inside that transaction.

Demo accounts use `Demo@12345`:

- `admin@smartcareer.vn`
- `hr1@smartcareer.vn` … `hr30@smartcareer.vn`
- `thanhtung.demo@smartcareer.vn`

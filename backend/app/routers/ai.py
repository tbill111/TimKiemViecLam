"""Router AI: ghép nối CV–JD, gợi ý việc, Skill Gap, xếp hạng ứng viên, gợi ý kỹ năng từ JD.

Phụ thuộc `app.deps` (Thái Anh): `get_current_user()` trả đối tượng có `.id`, `.role`, `.company_id`;
`require_role(*roles)` trả dependency kiểm tra vai trò và trả lại user.
"""
from __future__ import annotations

import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from app.ai.explain import generic_learning_steps
from app.ai.parser import suggest_skills
from app.ai.repository import AIRepository, get_ai_repo
from app.ai.scorers import score_many, score_pair
from app.ai.skills import SkillIndex
from app.ai.types import MODELS, CandidateInput, JobInput, ModelNotAvailable
from app.deps import require_role

router = APIRouter(tags=["ai"])

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "m3")


class ExtractSkillsIn(BaseModel):
    text: str = Field(min_length=1, max_length=20000)


class MatchIn(BaseModel):
    job_id: int
    model: Optional[str] = None
    candidate_id: Optional[int] = None  # chỉ dành cho nhà tuyển dụng / quản trị


def _model(name: Optional[str]) -> str:
    name = (name or DEFAULT_MODEL).lower()
    if name not in MODELS:
        raise HTTPException(422, detail={"detail": "invalid_model", "allowed": list(MODELS)})
    return name


def _score(model: str, cand: CandidateInput, job: JobInput) -> dict:
    try:
        return score_pair(model, cand, job)
    except ModelNotAvailable:
        raise HTTPException(503, detail="model_not_trained")


def _my_candidate(repo: AIRepository, user) -> CandidateInput:
    cand = repo.candidate_input_for_user(user.id)
    if cand is None:
        raise HTTPException(404, detail="candidate_profile_not_found")
    return cand


def _job_or_404(repo: AIRepository, job_id: int) -> JobInput:
    job = repo.job_input(job_id)
    if job is None:
        raise HTTPException(404, detail="job_not_found")
    return job


def _check_recruiter_owns(repo: AIRepository, user, job_id: int) -> None:
    if user.role == "admin":
        return
    if repo.job_company_id(job_id) != getattr(user, "company_id", None):
        raise HTTPException(403, detail="not_your_job")


@router.post("/ai/extract-skills")
async def extract_skills_from_jd(
    body: ExtractSkillsIn,
    user=Depends(require_role("recruiter", "admin")),
    repo: AIRepository = Depends(get_ai_repo),
):
    skills, aliases = repo.skill_index_rows()
    index = SkillIndex.from_rows(skills, aliases) if skills else None
    return {"skills": await run_in_threadpool(suggest_skills, body.text, index)}


@router.post("/ai/match")
async def match(
    body: MatchIn,
    user=Depends(require_role("candidate", "recruiter", "admin")),
    repo: AIRepository = Depends(get_ai_repo),
):
    model = _model(body.model)
    job = _job_or_404(repo, body.job_id)
    if user.role == "candidate":
        cand = _my_candidate(repo, user)
        if body.candidate_id is not None and body.candidate_id != cand.id:
            raise HTTPException(403, detail="not_your_profile")
    else:
        if body.candidate_id is None:
            raise HTTPException(422, detail="candidate_id_required")
        _check_recruiter_owns(repo, user, body.job_id)
        if user.role == "recruiter" and not any(a.candidate.id == body.candidate_id for a in repo.applicants_for_job(body.job_id)):
            raise HTTPException(403, detail="candidate_has_not_applied")
        found = repo.candidate_input(body.candidate_id)
        if found is None:
            raise HTTPException(404, detail="candidate_not_found")
        cand = found
    result = await run_in_threadpool(_score, model, cand, job)
    repo.save_match(cand.id, job.id, result)
    return result


@router.get("/candidates/me/matches")
async def my_matches(
    model: Optional[str] = Query(None),
    user=Depends(require_role("candidate")),
    repo: AIRepository = Depends(get_ai_repo),
):
    """Điểm khớp của hồ sơ với mọi tin đang mở (thay cho getAllMatchScores ở frontend)."""
    model = _model(model)
    cand = _my_candidate(repo, user)
    jobs = repo.open_jobs()
    try:
        results = await run_in_threadpool(score_many, model, cand, jobs)
    except ModelNotAvailable:
        raise HTTPException(503, detail="model_not_trained")
    return {"items": [{"job_id": j.id, "match": r} for j, r in zip(jobs, results)]}


@router.get("/candidates/me/recommendations")
async def recommendations(
    top: int = Query(10, ge=1, le=100),
    model: Optional[str] = Query(None),
    user=Depends(require_role("candidate")),
    repo: AIRepository = Depends(get_ai_repo),
):
    data = await my_matches(model, user, repo)
    ranked = sorted(data["items"], key=lambda it: it["match"]["total_score"], reverse=True)
    return {"items": ranked[:top]}


@router.get("/candidates/me/skill-gap")
async def skill_gap(
    job_id: int = Query(...),
    user=Depends(require_role("candidate")),
    repo: AIRepository = Depends(get_ai_repo),
):
    """Kỹ năng còn thiếu so với tin mục tiêu: bắt buộc trước, rồi theo số tin đang yêu cầu kỹ năng đó."""
    cand = _my_candidate(repo, user)
    job = _job_or_404(repo, job_id)
    result = await run_in_threadpool(_score, _model(None), cand, job)
    items = [
        {
            "skill": s,
            "required": required,
            "jobs_demanding": repo.open_jobs_requiring(s),
            "learning_steps": repo.learning_steps(s) or generic_learning_steps(s),
        }
        for required, group in ((True, result["missing_required"]), (False, result["missing_preferred"]))
        for s in group
    ]
    items.sort(key=lambda it: (not it["required"], -it["jobs_demanding"], it["skill"]))
    return {"job_id": job_id, "match_score": result["total_score"], "missing": items}


@router.get("/jobs/{job_id}/ranked-candidates")
async def ranked_candidates(
    job_id: int,
    top: int = Query(20, ge=1, le=200),
    model: Optional[str] = Query(None),
    user=Depends(require_role("recruiter", "admin")),
    repo: AIRepository = Depends(get_ai_repo),
):
    """Ứng viên ĐÃ NỘP vào tin của công ty mình, xếp theo điểm khớp. Tên chỉ để hiển thị, không dùng làm đặc trưng."""
    model = _model(model)
    job = _job_or_404(repo, job_id)
    _check_recruiter_owns(repo, user, job_id)
    rows = repo.applicants_for_job(job_id)
    items = []
    for row in rows:
        items.append(
            {
                "candidate_id": row.candidate.id,
                "full_name": row.full_name,
                "application_id": row.application_id,
                "status": row.status,
                "applied_at": row.applied_at,
                "match": await run_in_threadpool(_score, model, row.candidate, job),
            }
        )
    items.sort(key=lambda it: it["match"]["total_score"], reverse=True)
    return {"job_id": job_id, "items": items[:top]}

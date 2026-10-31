"""Router CV: tải CV, phân tích và trả kỹ năng đề xuất để ứng viên xác nhận."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from starlette.concurrency import run_in_threadpool

from app.ai.parser import MAX_CV_SIZE, parse_cv
from app.ai.repository import AIRepository, get_ai_repo
from app.ai.skills import SkillIndex
from app.ai.types import CvError
from app.deps import require_role

router = APIRouter(tags=["resumes"])

_STATUS = {"unsupported_type": 415, "too_large": 413, "no_text": 422, "corrupt": 422}


@router.post("/resumes/upload")
async def upload_resume(
    file: UploadFile = File(...),
    consent: bool = Form(False),
    user=Depends(require_role("candidate")),
    repo: AIRepository = Depends(get_ai_repo),
):
    """CV chỉ được lưu khi ứng viên đồng ý xử lý dữ liệu (`consent=true`)."""
    if not consent:
        raise HTTPException(400, detail="consent_required")
    data = await file.read(MAX_CV_SIZE + 1)
    skills, aliases = repo.skill_index_rows()
    index = SkillIndex.from_rows(skills, aliases) if skills else None
    try:
        parsed = await run_in_threadpool(parse_cv, data, file.filename or "", index)
    except CvError as err:
        raise HTTPException(_STATUS.get(err.code, 422), detail=err.code)
    resume_id = repo.save_resume(user.id, file.filename or "", parsed, consent)
    return {
        "resume_id": resume_id,
        "skills": parsed["skills"],  # [{name, source, confidence}] – ứng viên xác nhận ở bước sau
        "years_exp": parsed["years_exp"],
        "education_level": parsed["education_level"],
        "sections_found": sorted(k for k in parsed["sections"] if k != "header"),
    }

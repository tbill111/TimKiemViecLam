"""Database models for SmartCareer."""
from .entities import (
    Application,
    ApplicationStatusHistory,
    Candidate,
    CandidateSkill,
    Company,
    Job,
    JobSkill,
    Location,
    MatchResult,
    Recruiter,
    Resume,
    SavedJob,
    Skill,
    SkillAlias,
    User,
)

__all__ = [
    "Application", "ApplicationStatusHistory", "Candidate", "CandidateSkill", "Company",
    "Job", "JobSkill", "Location", "MatchResult", "Recruiter", "Resume", "SavedJob",
    "Skill", "SkillAlias", "User",
]

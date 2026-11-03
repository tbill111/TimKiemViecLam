import { sampleCandidates } from '../data/candidates';
import { sampleJobs } from '../data/jobs';
import type { Job } from '../types';
import { calculateSkillMatch } from '../utils';
import type { BiRow, BiSummary } from './bi';
import type { RankedCandidate } from './employer';

/** Dữ liệu minh hoạ cho chế độ demo không backend (VITE_OFFLINE_DEMO=true). */
const STATUS_CYCLE = ['applied', 'screening', 'interview', 'applied', 'offer', 'screening', 'rejected', 'hired'];

export function demoRankedCandidates(job: Job): RankedCandidate[] {
  return sampleCandidates
    .map((candidate, index) => {
      const result = calculateSkillMatch(candidate, job);
      return {
        candidate_id: index + 1,
        full_name: candidate.fullName,
        application_id: Number(job.id.replace(/\D/g, '') || 0) * 100 + index + 1,
        status: STATUS_CYCLE[index % STATUS_CYCLE.length],
        applied_at: new Date(Date.UTC(2026, 9, 1 + index)).toISOString().replace('Z', ''),
        match: {
          total_score: result.matchScore,
          matched_required: result.matchedSkills,
          missing_required: result.missingSkills,
          explanation: `Khớp ${result.matchScore}/100. ${result.matchedSkills.length ? `Đã có ${result.matchedSkills.join(', ')}.` : 'Chưa có kỹ năng bắt buộc nào.'}${result.missingSkills.length ? ` Thiếu ${result.missingSkills.join(', ')}.` : ''}`,
        },
      };
    })
    .sort((a, b) => b.match.total_score - a.match.total_score);
}

export function demoBi(): { summary: BiSummary; skills: BiRow[]; salary: BiRow[]; stages: BiRow[] } {
  const demand = new Map<string, number>();
  for (const job of sampleJobs) for (const skill of job.requiredSkills) demand.set(skill, (demand.get(skill) ?? 0) + 1);
  const skills: BiRow[] = [...demand.entries()].map(([skill, open]) => ({
    skill_name: skill,
    open_job_count: open,
    candidate_count: sampleCandidates.filter((c) => c.skills.includes(skill)).length,
  }));

  const salaryRows: BiRow[] = sampleJobs
    .filter((job) => job.salaryMin != null && job.salaryMax != null)
    .map((job) => ({ posted_month: job.postedAt.slice(0, 7), job_count: 1, average_salary_min: job.salaryMin ?? 0, average_salary_max: job.salaryMax ?? 0 }));

  const counts = new Map<string, number>();
  const firstJob = sampleJobs[0];
  for (const item of demoRankedCandidates(firstJob)) counts.set(item.status, (counts.get(item.status) ?? 0) + 1);
  const order = ['applied', 'screening', 'interview', 'offer', 'hired', 'rejected'];
  const reached = (index: number) => order.slice(index, 5).reduce((sum, stage) => sum + (counts.get(stage) ?? 0), 0);
  const stages: BiRow[] = order.map((stage, index) => ({
    stage,
    stage_order: index + 1,
    applications: stage === 'rejected' ? counts.get('rejected') ?? 0 : reached(index),
  }));
  const applications = stages[0].applications as number;
  const hired = stages[4].applications as number;
  return {
    summary: { candidates: sampleCandidates.length, open_jobs: sampleJobs.length, applications, hire_rate: applications ? Math.round((hired / applications) * 1000) / 10 : 0 },
    skills,
    salary: salaryRows,
    stages,
  };
}

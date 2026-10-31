import type { Job, StudentProfile, SkillMatchResult, FilterState, DataQualityMetrics, MatchProfile } from '../types';
import { sampleJobs } from '../data/jobs';

/** Mốc ngày của dữ liệu demo; cố định để nhãn "X ngày trước" không đổi theo ngày chạy thật. */
export const DEMO_NOW = new Date('2026-10-22T12:00:00Z');

/** Điểm tối thiểu để một công việc được coi là "phù hợp" với hồ sơ. */
export const SUITABLE_THRESHOLD = 50;

// ============================================================
// SKILL MATCHING
// ============================================================

const normalizeSkill = (s: string) => s.toLowerCase().replace(/\s+/g, ' ').trim();

/** Bỏ hậu tố "cơ bản" để "Python cơ bản" và "Python" được coi là cùng kỹ năng. */
const stripLevel = (s: string) => s.replace(/\s+cơ bản$/, '').trim();

/** Tách kỹ năng có nhiều lựa chọn: "React hoặc Node.js" → ["react", "node.js"]. */
const alternatives = (skill: string) =>
  normalizeSkill(skill)
    .split(/\s+hoặc\s+|\//)
    .map((s) => stripLevel(s.trim()))
    .filter(Boolean);

/**
 * Kiểm tra một kỹ năng có trong danh sách kỹ năng của hồ sơ hay không.
 * So khớp nguyên tên kỹ năng (không phân biệt hoa/thường, bỏ hậu tố "cơ bản"),
 * và chấp nhận một trong các lựa chọn khi yêu cầu có dạng "A hoặc B" hay "A/B".
 * Không khớp một phần chuỗi, để "React" không bị coi là có "React Query".
 */
export function hasSkill(profileSkills: string[], skill: string): boolean {
  const owned = new Set(profileSkills.map((s) => stripLevel(normalizeSkill(s))));
  return alternatives(skill).some((alt) => owned.has(alt));
}

/** Trọng số của thuật toán ghép nối đa tiêu chí (tổng = 1). */
export const MATCH_WEIGHTS = {
  required: 0.6,
  preferred: 0.25,
  preference: 0.15,
} as const;

/** Tách danh sách kỹ năng yêu cầu thành nhóm đã có và còn thiếu. */
function splitSkills(profileSkills: string[], skills: string[]): { matched: string[]; missing: string[] } {
  const matched: string[] = [];
  const missing: string[] = [];
  for (const skill of skills) {
    if (hasSkill(profileSkills, skill)) matched.push(skill);
    else missing.push(skill);
  }
  return { matched, missing };
}

const percent = (part: number, total: number) => (total === 0 ? 0 : Math.round((part / total) * 100));

/**
 * Tính điểm phù hợp giữa hồ sơ và một công việc theo 3 tiêu chí có trọng số:
 *   - Kỹ năng bắt buộc (60%): số kỹ năng bắt buộc đáp ứng / tổng kỹ năng bắt buộc
 *   - Kỹ năng ưu tiên  (25%): số kỹ năng ưu tiên đáp ứng / tổng kỹ năng ưu tiên
 *   - Mong muốn        (15%): 50 điểm nếu đúng địa điểm, 50 điểm nếu đúng hình thức làm việc
 * Nếu công việc không có kỹ năng ưu tiên, phần 25% được tính theo điểm kỹ năng bắt buộc.
 * Kết quả xác định (không ngẫu nhiên): cùng hồ sơ và công việc luôn cho cùng điểm.
 */
export function calculateSkillMatch(profile: MatchProfile, job: Job): SkillMatchResult {
  const required = splitSkills(profile.skills, job.requiredSkills);
  const preferred = splitSkills(profile.skills, job.preferredSkills);

  const requiredScore = percent(required.matched.length, job.requiredSkills.length);
  const preferredScore =
    job.preferredSkills.length === 0 ? requiredScore : percent(preferred.matched.length, job.preferredSkills.length);

  const locationMatch = profile.preferredLocations.includes(job.location);
  const workTypeMatch = profile.preferredWorkTypes.includes(job.workType);
  const preferenceScore = (locationMatch ? 50 : 0) + (workTypeMatch ? 50 : 0);

  const matchScore = Math.round(
    requiredScore * MATCH_WEIGHTS.required +
      preferredScore * MATCH_WEIGHTS.preferred +
      preferenceScore * MATCH_WEIGHTS.preference
  );

  return {
    jobId: job.id,
    matchScore,
    matchedSkills: required.matched,
    missingSkills: required.missing,
    totalRequired: job.requiredSkills.length,
    matchedPreferred: preferred.matched,
    missingPreferred: preferred.missing,
    requiredScore,
    preferredScore,
    preferenceScore,
    locationMatch,
    workTypeMatch,
  };
}

/**
 * Số công việc mẫu có điểm phù hợp đạt ngưỡng SUITABLE_THRESHOLD.
 */
export function countSuitableJobs(profile: StudentProfile): number {
  return sampleJobs.filter((job) => calculateSkillMatch(profile, job).matchScore >= SUITABLE_THRESHOLD).length;
}

/**
 * Số tin mẫu có kỹ năng cho trước (ở mục yêu cầu hoặc ưu tiên).
 * Trả về cả số tin yêu cầu bắt buộc để hiển thị chi tiết.
 */
export function countJobsWithSkill(skill: string): { anywhere: number; required: number } {
  const target = normalizeSkill(skill);
  const has = (list: string[]) => list.some((s) => normalizeSkill(s) === target);
  return {
    anywhere: sampleJobs.filter((j) => has(j.requiredSkills) || has(j.preferredSkills)).length,
    required: sampleJobs.filter((j) => has(j.requiredSkills)).length,
  };
}

/**
 * Tỷ lệ phần trăm kỹ năng trong một nhóm mà hồ sơ đã có.
 */
export function getSkillCoverage(profile: StudentProfile, skills: string[]): number {
  if (skills.length === 0) return 0;
  const covered = skills.filter((s) => hasSkill(profile.skills, s)).length;
  return Math.round((covered / skills.length) * 100);
}

/**
 * Tính điểm phù hợp cho tất cả công việc và trả về đã sắp xếp.
 */
export function getAllMatchScores(profile: StudentProfile): Map<string, SkillMatchResult> {
  const map = new Map<string, SkillMatchResult>();
  for (const job of sampleJobs) {
    map.set(job.id, calculateSkillMatch(profile, job));
  }
  return map;
}

/**
 * Lấy màu badge dựa trên điểm phù hợp.
 */
export function getMatchColorClass(score: number): string {
  if (score >= 80) return 'match-excellent';
  if (score >= 60) return 'match-good';
  if (score >= 40) return 'match-fair';
  return 'match-poor';
}

// ============================================================
// JOB FILTERING
// ============================================================

/**
 * Lọc và sắp xếp danh sách công việc theo bộ lọc.
 */
export function filterJobs(
  jobs: Job[],
  filters: FilterState,
  matchScores: Map<string, SkillMatchResult>
): Job[] {
  const query = filters.query.toLowerCase().trim();

  let result = jobs.filter((job) => {
    if (query) {
      const searchable = [
        job.title,
        job.company,
        job.location,
        job.category,
        ...job.requiredSkills,
        ...job.preferredSkills,
      ]
        .join(' ')
        .toLowerCase();
      if (!searchable.includes(query)) return false;
    }

    if (filters.location && filters.location !== 'Tất cả') {
      if (job.location !== filters.location) return false;
    }

    if (filters.workType && job.workType !== filters.workType) return false;

    if (filters.experienceLevel && job.experienceLevel !== filters.experienceLevel) return false;

    if (filters.category && job.category !== filters.category) return false;

    return true;
  });

  if (filters.sortBy === 'relevance') {
    result = result.sort((a, b) => {
      const scoreA = matchScores.get(a.id)?.matchScore ?? 0;
      const scoreB = matchScores.get(b.id)?.matchScore ?? 0;
      return scoreB - scoreA;
    });
  } else {
    result = result.sort(
      (a, b) => new Date(b.postedAt).getTime() - new Date(a.postedAt).getTime()
    );
  }

  return result;
}

// ============================================================
// DATE FORMATTING
// ============================================================

/**
 * Format ngày ISO thành dạng tương đối tiếng Việt (ví dụ: "3 ngày trước").
 */
export function formatRelativeDate(isoDate: string): string {
  const date = new Date(isoDate);
  const now = DEMO_NOW;
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return 'Hôm nay';
  if (diffDays === 1) return '1 ngày trước';
  if (diffDays < 7) return `${diffDays} ngày trước`;
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} tuần trước`;
  return `${Math.floor(diffDays / 30)} tháng trước`;
}

/**
 * Format ngày ISO thành dạng dd/MM/yyyy.
 */
export function formatDate(isoDate: string): string {
  const date = new Date(isoDate);
  return date.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

// ============================================================
// PROFILE COMPLETION
// ============================================================

/**
 * Tính phần trăm hoàn thiện hồ sơ dựa trên các trường đã điền.
 */
export function calculateProfileCompletion(profile: StudentProfile): number {
  const checks = [
    profile.fullName.trim() !== '',
    profile.university.trim() !== '',
    profile.major.trim() !== '',
    profile.year.trim() !== '',
    profile.email.trim() !== '',
    profile.careerGoal.trim() !== '',
    profile.skills.length >= 3,
    profile.languages.length >= 1,
    profile.projects.length >= 1,
    profile.experience.length >= 1,
    profile.certificates.length >= 1,
    profile.phone !== undefined && profile.phone.trim() !== '',
  ];
  const passed = checks.filter(Boolean).length;
  return Math.round((passed / checks.length) * 100);
}

// ============================================================
// UNIQUE LOCATIONS FROM JOBS
// ============================================================

export function getUniqueLocations(jobs: Job[]): string[] {
  const locs = Array.from(new Set(jobs.map((j) => j.location)));
  return ['Tất cả', ...locs.sort()];
}

// ============================================================
// DATA QUALITY (tính từ dataset mẫu)
// ============================================================

/**
 * Kiểm tra chất lượng dataset mẫu theo các quy tắc Transform đã mô tả:
 * thiếu trường bắt buộc, trùng lặp (cùng id hoặc cùng tên + công ty).
 * Mỗi bản ghi chỉ được tính một lần: hợp lệ hoặc không hợp lệ.
 */
export function getDataQualityMetrics(profile: StudentProfile, jobs: Job[]): DataQualityMetrics {
  const seenIds = new Set<string>();
  const seenTitleCompany = new Set<string>();
  let duplicateRecords = 0;
  let missingFieldRecords = 0;
  let validRecords = 0;

  for (const job of jobs) {
    const key = `${job.title}|${job.company}`.toLowerCase();
    const isDuplicate = seenIds.has(job.id) || seenTitleCompany.has(key);
    const isMissing =
      !job.description.trim() ||
      !job.salary.trim() ||
      job.requiredSkills.length === 0 ||
      job.responsibilities.length === 0;

    seenIds.add(job.id);
    seenTitleCompany.add(key);

    if (isDuplicate) duplicateRecords++;
    else if (isMissing) missingFieldRecords++;
    else validRecords++;
  }

  // Hồ sơ sinh viên được tính là một bản ghi
  const profileMissing = !profile.careerGoal.trim() || profile.skills.length === 0;
  if (profileMissing) missingFieldRecords++;
  else validRecords++;

  return {
    totalRecords: jobs.length + 1,
    validRecords,
    duplicateRecords,
    missingFieldRecords,
    lastUpdated: DEMO_NOW.toISOString(),
  };
}

/**
 * Số bản ghi mẫu cho từng nhóm nguồn dữ liệu, tính từ dataset hiện có.
 * Nguồn ngoài và nguồn từ nhà trường chưa được kết nối nên bằng 0.
 * `behaviorCount` là số sự kiện hành vi hiện có (việc đã lưu + đơn ứng tuyển).
 */
export function getSourceRecordCounts(profile: StudentProfile, jobs: Job[], behaviorCount: number): Record<string, number> {
  const skillSet = new Set<string>();
  for (const job of jobs) {
    job.requiredSkills.forEach((s) => skillSet.add(normalizeSkill(s)));
    job.preferredSkills.forEach((s) => skillSet.add(normalizeSkill(s)));
  }
  profile.skills.forEach((s) => skillSet.add(normalizeSkill(s)));

  return {
    'ds-001': 1,
    'ds-002': jobs.length,
    'ds-003': 0,
    'ds-004': skillSet.size,
    'ds-005': behaviorCount,
    'ds-006': 0,
  };
}

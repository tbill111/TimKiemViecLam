// ============================================================
// CORE DATA TYPES
// ============================================================

export type WorkType = 'Toàn thời gian' | 'Bán thời gian' | 'Thực tập' | 'Remote';
export type ExperienceLevel = 'Chưa có kinh nghiệm' | 'Dưới 1 năm' | '1-2 năm' | '2-3 năm' | '3+ năm';
export type JobCategory =
  | 'Frontend Development'
  | 'Backend Development'
  | 'Data Science & Analytics'
  | 'Business Analysis'
  | 'QA & Testing'
  | 'UI/UX Design'
  | 'IT Support'
  | 'Digital Marketing'
  | 'Software Engineering'
  | 'Business Operations';

/** 6 trạng thái theo phễu tuyển dụng: applied → screening → interview → offer → hired, và rejected ở bất kỳ bước chưa kết thúc. */
export type ApplicationStatus =
  | 'Đã ứng tuyển'
  | 'Đang xem xét'
  | 'Phỏng vấn'
  | 'Đề nghị'
  | 'Đã tuyển'
  | 'Từ chối';

export type SkillPriority = 'Cao' | 'Trung bình' | 'Thấp';

// ============================================================
// JOB TYPES
// ============================================================

export interface Job {
  id: string;
  title: string;
  company: string;
  location: string;
  workType: WorkType;
  experienceLevel: ExperienceLevel;
  salary: string;
  description: string;
  responsibilities: string[];
  requiredSkills: string[];
  preferredSkills: string[];
  postedAt: string; // ISO date string
  category: JobCategory;
  companySize?: string;
  companyIndustry?: string;
  /** Dữ liệu số từ backend (triệu VNĐ/tháng); null = thỏa thuận. */
  salaryMin?: number | null;
  salaryMax?: number | null;
  status?: 'open' | 'closed';
}

// ============================================================
// STUDENT PROFILE TYPES
// ============================================================

export interface Project {
  id: string;
  name: string;
  description: string;
  technologies: string[];
  url?: string;
}

export interface Experience {
  id: string;
  position: string;
  company: string;
  duration: string;
  description: string;
}

export interface Certificate {
  id: string;
  name: string;
  issuer: string;
  year: string;
}

export interface StudentProfile {
  fullName: string;
  university: string;
  major: string;
  year: string;
  email: string;
  phone?: string;
  /** Liên kết hồ sơ GitHub, LinkedIn: chỉ để hiển thị, không lấy dữ liệu từ các trang này. */
  githubUrl?: string;
  linkedinUrl?: string;
  careerGoal: string;
  skills: string[];
  /** Địa điểm mong muốn, dùng cho tiêu chí "phù hợp mong muốn" khi ghép nối. */
  preferredLocations: string[];
  /** Hình thức làm việc mong muốn. */
  preferredWorkTypes: WorkType[];
  languages: string[];
  projects: Project[];
  experience: Experience[];
  certificates: Certificate[];
  profileCompletion: number;
}

// ============================================================
// APPLICATION & SAVED JOBS
// ============================================================

export interface Application {
  id: string;
  jobId: string;
  appliedAt: string; // ISO date string
  status: ApplicationStatus;
  notes?: string;
}

export interface SavedJob {
  jobId: string;
  savedAt: string; // ISO date string
}

// ============================================================
// SKILL ANALYSIS TYPES
// ============================================================

export interface SkillMatchResult {
  jobId: string;
  /** Điểm tổng hợp có trọng số, 0–100. */
  matchScore: number;
  /** Kỹ năng bắt buộc đã có / còn thiếu. */
  matchedSkills: string[];
  missingSkills: string[];
  totalRequired: number;
  /** Kỹ năng ưu tiên đã có / còn thiếu. */
  matchedPreferred: string[];
  missingPreferred: string[];
  /** Điểm thành phần, 0–100. */
  requiredScore: number;
  preferredScore: number;
  preferenceScore: number;
  locationMatch: boolean;
  workTypeMatch: boolean;
  /** Chỉ có khi điểm do backend (mô hình M1–M4) tính: điểm thành phần 0–100 và câu giải thích. */
  semanticScore?: number | null;
  expScore?: number | null;
  eduScore?: number | null;
  explanation?: string;
  model?: string;
  /** Phiên bản model của backend, ví dụ `m4-SYNTHETIC-labels` khi M4 được huấn luyện trên nhãn mô phỏng. */
  modelVersion?: string;
}

/** Phần hồ sơ đủ để tính điểm ghép nối (dùng chung cho sinh viên và ứng viên mẫu). */
export type MatchProfile = Pick<StudentProfile, 'skills' | 'preferredLocations' | 'preferredWorkTypes'>;

/** Ứng viên mẫu hiển thị ở cổng nhà tuyển dụng. */
export interface Candidate extends MatchProfile {
  id: string;
  fullName: string;
  major: string;
  university: string;
  year: string;
}

export interface SkillGapItem {
  id: string;
  skill: string;
  priority: SkillPriority;
  category: string;
  learned: boolean;
  learningSteps: string[];
}

// ============================================================
// ETL / DATA FLOW TYPES
// ============================================================

export interface DataQualityMetrics {
  totalRecords: number;
  validRecords: number;
  duplicateRecords: number;
  missingFieldRecords: number;
  lastUpdated: string;
}

export interface DataSource {
  id: string;
  name: string;
  description: string;
  type: 'internal' | 'external' | 'partner';
  /** Định dạng dữ liệu đầu vào, ví dụ "Biểu mẫu web, PDF/DOCX". */
  format: string;
  fields: string[];
  status: 'active' | 'pending' | 'inactive';
}

/** Bản ghi tin tuyển dụng thô, chưa làm sạch, như khi vừa thu thập từ nhiều nguồn. */
export interface RawJobRecord {
  id: string;
  source: 'Doanh nghiệp' | 'Đối tác' | 'Tệp CSV';
  title: string;
  company: string;
  location: string;
  workType: string;
  /** Kỹ năng dạng chuỗi, phân tách bằng dấu phẩy hoặc chấm phẩy. */
  skills: string;
  salary: string;
  deadline: string; // ISO date
  contactEmail: string;
}

export type PipelineStatus = 'clean' | 'rejected' | 'duplicate' | 'expired';

/** Kết quả xử lý một bản ghi qua pipeline làm sạch. */
export interface PipelineRecord {
  raw: RawJobRecord;
  status: PipelineStatus;
  /** Lý do bị loại (nếu có). */
  reason?: string;
  /** Các thay đổi đã áp dụng, ví dụ "Địa điểm: HN → Hà Nội". */
  changes: string[];
  location: string;
  workType: string;
  skills: string[];
  salary: string;
}

export interface PipelineSummary {
  total: number;
  clean: number;
  rejected: number;
  duplicate: number;
  expired: number;
  /** Tổng số trường đã được chuẩn hóa trên các bản ghi giữ lại. */
  normalizedFields: number;
}

// ============================================================
// APP STATE TYPES
// ============================================================

export interface AppState {
  savedJobs: SavedJob[];
  applications: Application[];
  studentProfile: StudentProfile;
  skillGapItems: SkillGapItem[];
}

export interface FilterState {
  query: string;
  location: string;
  workType: WorkType | '';
  experienceLevel: ExperienceLevel | '';
  category: JobCategory | '';
  sortBy: 'relevance' | 'newest';
}

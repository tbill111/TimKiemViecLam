import type { PipelineRecord, PipelineSummary, RawJobRecord } from '../types';
import { skillAliases } from '../data/skillCatalog';
import { DEMO_NOW } from './index';

// ============================================================
// BẢNG QUY TẮC CHUẨN HÓA
// ============================================================

const LOCATION_MAP: Record<string, string> = {
  'hn': 'Hà Nội', 'ha noi': 'Hà Nội', 'hà nội': 'Hà Nội', 'tp. hà nội': 'Hà Nội', 'tp hà nội': 'Hà Nội',
  'hcm': 'Hồ Chí Minh', 'tp.hcm': 'Hồ Chí Minh', 'tp hcm': 'Hồ Chí Minh', 'sài gòn': 'Hồ Chí Minh',
  'sai gon': 'Hồ Chí Minh', 'hồ chí minh': 'Hồ Chí Minh',
  'đà nẵng': 'Đà Nẵng', 'da nang': 'Đà Nẵng',
  'remote': 'Remote', 'từ xa': 'Remote',
};

const WORK_TYPE_MAP: Record<string, string> = {
  'intern': 'Thực tập', 'internship': 'Thực tập', 'thực tập sinh': 'Thực tập', 'thực tập': 'Thực tập',
  'full-time': 'Toàn thời gian', 'fulltime': 'Toàn thời gian', 'toàn thời gian': 'Toàn thời gian',
  'part-time': 'Bán thời gian', 'bán thời gian': 'Bán thời gian',
  'remote': 'Remote',
};

const EMAIL_RE = /^[\w.+-]+@[\w-]+(\.[\w-]+)+$/;

const key = (s: string) => s.trim().toLowerCase();

/** Đưa tên kỹ năng về tên chuẩn theo bảng từ đồng nghĩa; giữ nguyên nếu không có trong bảng. */
function canonicalSkill(raw: string): string {
  const k = key(raw);
  for (const [name, aliases] of Object.entries(skillAliases)) {
    if (key(name) === k || aliases.includes(k)) return name;
  }
  return raw.trim();
}

// ============================================================
// PIPELINE: Validate → Transform → Loại trùng → Kiểm tra hạn
// ============================================================

/**
 * Chạy quy trình làm sạch trên dữ liệu thô và ghi lại từng thay đổi.
 * Mỗi bản ghi kết thúc ở một trạng thái: sạch, bị loại, trùng lặp hoặc hết hạn.
 */
export function runCleaningPipeline(records: RawJobRecord[], now: Date = DEMO_NOW): {
  records: PipelineRecord[];
  summary: PipelineSummary;
} {
  // 1. Validate: trường bắt buộc và định dạng email
  const results: PipelineRecord[] = records.map((raw) => {
    const missing = [
      !raw.title.trim() && 'tên vị trí',
      !raw.company.trim() && 'công ty',
      !raw.skills.trim() && 'kỹ năng',
    ].filter(Boolean);
    const base = { raw, changes: [], location: raw.location, workType: raw.workType, skills: [], salary: raw.salary };
    if (missing.length > 0) return { ...base, status: 'rejected', reason: `Thiếu trường bắt buộc: ${missing.join(', ')}` };
    if (!EMAIL_RE.test(raw.contactEmail)) return { ...base, status: 'rejected', reason: 'Email liên hệ sai định dạng' };
    return { ...base, status: 'clean' };
  });

  // 2. Transform: chuẩn hóa địa điểm, hình thức, kỹ năng, mức lương
  for (const r of results) {
    if (r.status === 'rejected') continue;
    const location = LOCATION_MAP[key(r.raw.location)] ?? r.raw.location.trim();
    if (location !== r.raw.location) r.changes.push(`Địa điểm: ${r.raw.location} → ${location}`);
    r.location = location;

    const workType = WORK_TYPE_MAP[key(r.raw.workType)] ?? r.raw.workType.trim();
    if (workType !== r.raw.workType) r.changes.push(`Hình thức: ${r.raw.workType} → ${workType}`);
    r.workType = workType;

    const rawSkills = r.raw.skills.split(/[,;]/).map((s) => s.trim()).filter(Boolean);
    const skills: string[] = [];
    for (const s of rawSkills) {
      const name = canonicalSkill(s);
      if (name !== s) r.changes.push(`Kỹ năng: ${s} → ${name}`);
      if (!skills.includes(name)) skills.push(name);
    }
    r.skills = skills;

    if (!r.raw.salary.trim()) {
      r.salary = 'Thỏa thuận';
      r.changes.push('Mức lương: (trống) → Thỏa thuận');
    }
  }

  // 3. Loại trùng: cùng tên vị trí và công ty, giữ tin có hạn nộp muộn nhất
  const groups = new Map<string, PipelineRecord[]>();
  for (const r of results) {
    if (r.status === 'rejected') continue;
    const k = `${key(r.raw.title)}|${key(r.raw.company)}`;
    groups.set(k, [...(groups.get(k) ?? []), r]);
  }
  for (const group of groups.values()) {
    if (group.length < 2) continue;
    const kept = group.reduce((a, b) => (b.raw.deadline > a.raw.deadline ? b : a));
    for (const r of group) {
      if (r !== kept) {
        r.status = 'duplicate';
        r.reason = `Trùng với ${kept.raw.id}`;
      }
    }
  }

  // 4. Kiểm tra hạn nộp: tin hết hạn bị ẩn khỏi tìm kiếm
  for (const r of results) {
    if (r.status === 'clean' && new Date(r.raw.deadline) < now) {
      r.status = 'expired';
      r.reason = 'Hết hạn nộp, ẩn khỏi tìm kiếm';
    }
  }

  const count = (s: PipelineRecord['status']) => results.filter((r) => r.status === s).length;
  return {
    records: results,
    summary: {
      total: results.length,
      clean: count('clean'),
      rejected: count('rejected'),
      duplicate: count('duplicate'),
      expired: count('expired'),
      normalizedFields: results.filter((r) => r.status === 'clean').reduce((n, r) => n + r.changes.length, 0),
    },
  };
}

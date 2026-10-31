import { useState } from 'react';
import {
  UserCircle,
  Edit3,
  Save,
  X,
  Plus,
  GraduationCap,
  Briefcase,
  Award,
  Code2,
  Target,
  CheckCircle2,
  Trash2,
  MapPin,
  Link2,
} from 'lucide-react';
import type { UseAppState } from '../hooks/useAppState';
import CvImport from '../components/profile/CvImport';
import type { Certificate, Experience, Project, StudentProfile, WorkType } from '../types';

const LOCATION_OPTIONS = ['Hà Nội', 'Hồ Chí Minh', 'Đà Nẵng', 'Remote'];
const WORK_TYPE_OPTIONS: WorkType[] = ['Toàn thời gian', 'Bán thời gian', 'Thực tập', 'Remote'];

/** Thêm phần tử nếu chưa có, bỏ đi nếu đã có. */
function toggleItem<T>(list: T[], item: T): T[] {
  return list.includes(item) ? list.filter((x) => x !== item) : [...list, item];
}

interface ProfilePageProps {
  appState: UseAppState;
}

/** Thay phần tử tại vị trí `index` bằng bản đã gộp `patch`. */
function replaceAt<T>(list: T[], index: number, patch: Partial<T>): T[] {
  return list.map((item, i) => (i === index ? { ...item, ...patch } : item));
}

/** Xóa phần tử tại vị trí `index`. */
function removeAt<T>(list: T[], index: number): T[] {
  return list.filter((_, i) => i !== index);
}

/** Tách chuỗi "React, Node.js" thành mảng ["React", "Node.js"]. */
function parseList(raw: string): string[] {
  return raw.split(',').map((s) => s.trim()).filter(Boolean);
}

const newId = (prefix: string) => `${prefix}-${Date.now()}`;

export default function ProfilePage({ appState }: ProfilePageProps) {
  const { studentProfile, updateProfile } = appState;
  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState<StudentProfile>(studentProfile);
  const [newSkill, setNewSkill] = useState('');
  const [newLanguage, setNewLanguage] = useState('');
  const [saveSuccess, setSaveSuccess] = useState(false);

  const startEdit = () => {
    setEditData({ ...studentProfile });
    setIsEditing(true);
    setSaveSuccess(false);
  };

  const cancelEdit = () => {
    setIsEditing(false);
    setEditData(studentProfile);
  };

  const handleSave = () => {
    // Bỏ các mục để trống trước khi lưu
    updateProfile({
      ...editData,
      languages: editData.languages.filter((l) => l.trim()),
      projects: editData.projects.filter((p) => p.name.trim()),
      experience: editData.experience.filter((e) => e.position.trim()),
      certificates: editData.certificates.filter((c) => c.name.trim()),
    });
    setIsEditing(false);
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 3000);
  };

  const addSkill = () => {
    const skill = newSkill.trim();
    if (!skill || editData.skills.includes(skill)) return;
    setEditData((prev) => ({ ...prev, skills: [...prev.skills, skill] }));
    setNewSkill('');
  };

  const removeSkill = (skill: string) => {
    setEditData((prev) => ({ ...prev, skills: prev.skills.filter((s) => s !== skill) }));
  };

  const addLanguage = () => {
    const language = newLanguage.trim();
    if (!language) return;
    setEditData((prev) => ({ ...prev, languages: [...prev.languages, language] }));
    setNewLanguage('');
  };

  const updateField = <K extends keyof StudentProfile>(key: K, value: StudentProfile[K]) => {
    setEditData((prev) => ({ ...prev, [key]: value }));
  };

  const addProject = () => {
    const project: Project = { id: newId('proj'), name: '', description: '', technologies: [] };
    setEditData((prev) => ({ ...prev, projects: [...prev.projects, project] }));
  };

  const updateProject = (index: number, patch: Partial<Project>) => {
    setEditData((prev) => ({ ...prev, projects: replaceAt(prev.projects, index, patch) }));
  };

  const removeProject = (index: number) => {
    setEditData((prev) => ({ ...prev, projects: removeAt(prev.projects, index) }));
  };

  const addExperience = () => {
    const item: Experience = { id: newId('exp'), position: '', company: '', duration: '', description: '' };
    setEditData((prev) => ({ ...prev, experience: [...prev.experience, item] }));
  };

  const updateExperience = (index: number, patch: Partial<Experience>) => {
    setEditData((prev) => ({ ...prev, experience: replaceAt(prev.experience, index, patch) }));
  };

  const removeExperience = (index: number) => {
    setEditData((prev) => ({ ...prev, experience: removeAt(prev.experience, index) }));
  };

  const addCertificate = () => {
    const item: Certificate = { id: newId('cert'), name: '', issuer: '', year: '' };
    setEditData((prev) => ({ ...prev, certificates: [...prev.certificates, item] }));
  };

  const updateCertificate = (index: number, patch: Partial<Certificate>) => {
    setEditData((prev) => ({ ...prev, certificates: replaceAt(prev.certificates, index, patch) }));
  };

  const removeCertificate = (index: number) => {
    setEditData((prev) => ({ ...prev, certificates: removeAt(prev.certificates, index) }));
  };

  const profile = isEditing ? editData : studentProfile;

  const completionColor =
    studentProfile.profileCompletion >= 80
      ? 'bg-emerald-500'
      : studentProfile.profileCompletion >= 50
      ? 'bg-blue-500'
      : 'bg-amber-500';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Hồ sơ của tôi</h1>
          <p className="text-slate-500 text-sm mt-0.5">
            Thông tin được lưu trong trình duyệt (localStorage). Không gửi dữ liệu lên server.
          </p>
        </div>
        <div className="flex gap-2">
          {isEditing ? (
            <>
              <button onClick={handleSave} className="btn-primary">
                <Save size={16} />
                Lưu thay đổi
              </button>
              <button onClick={cancelEdit} className="btn-secondary">
                <X size={16} />
                Hủy
              </button>
            </>
          ) : (
            <button onClick={startEdit} className="btn-secondary">
              <Edit3 size={16} />
              Chỉnh sửa
            </button>
          )}
        </div>
      </div>

      {saveSuccess && (
        <div className="flex items-center gap-3 p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-700 text-sm">
          <CheckCircle2 size={16} />
          Hồ sơ đã được lưu thành công!
        </div>
      )}

      {/* Profile completion */}
      <div className="card p-5">
        <div className="flex items-center justify-between mb-2">
          <h2 className="section-title text-sm">Mức độ hoàn thiện hồ sơ</h2>
          <span className="text-lg font-bold text-slate-800">{studentProfile.profileCompletion}%</span>
        </div>
        <div className="progress-bar h-3">
          <div className={`progress-fill ${completionColor}`} style={{ width: `${studentProfile.profileCompletion}%` }} />
        </div>
        <p className="text-xs text-slate-400 mt-2">
          Hồ sơ càng hoàn thiện, điểm phù hợp khi ghép nối với việc làm càng chính xác.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Basic info */}
        <div className="lg:col-span-2 space-y-5">
          {/* Personal info */}
          <div className="card p-5">
            <div className="flex items-center gap-2 mb-4">
              <UserCircle size={18} className="text-blue-600" />
              <h2 className="section-title text-sm">Thông tin cá nhân</h2>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-500 mb-1.5">Họ và tên</label>
                {isEditing ? (
                  <input className="input-field" value={editData.fullName} onChange={(e) => updateField('fullName', e.target.value)} />
                ) : (
                  <div className="text-sm font-medium text-slate-800">{profile.fullName}</div>
                )}
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-500 mb-1.5">Email (demo)</label>
                {isEditing ? (
                  <input className="input-field" value={editData.email} onChange={(e) => updateField('email', e.target.value)} />
                ) : (
                  <div className="text-sm text-slate-800">{profile.email}</div>
                )}
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-500 mb-1.5">Trường đại học</label>
                {isEditing ? (
                  <input className="input-field" value={editData.university} onChange={(e) => updateField('university', e.target.value)} />
                ) : (
                  <div className="text-sm text-slate-800">{profile.university}</div>
                )}
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-500 mb-1.5">Chuyên ngành</label>
                {isEditing ? (
                  <input className="input-field" value={editData.major} onChange={(e) => updateField('major', e.target.value)} />
                ) : (
                  <div className="text-sm text-slate-800">{profile.major}</div>
                )}
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-500 mb-1.5">Năm học</label>
                {isEditing ? (
                  <input className="input-field" value={editData.year} onChange={(e) => updateField('year', e.target.value)} />
                ) : (
                  <div className="text-sm text-slate-800">{profile.year}</div>
                )}
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-500 mb-1.5">Số điện thoại (demo)</label>
                {isEditing ? (
                  <input className="input-field" value={editData.phone ?? ''} onChange={(e) => updateField('phone', e.target.value)} />
                ) : (
                  <div className="text-sm text-slate-800">{profile.phone ?? '—'}</div>
                )}
              </div>
            </div>
            <div className="mt-4">
              <label className="block text-xs font-medium text-slate-500 mb-1.5">Mục tiêu nghề nghiệp</label>
              {isEditing ? (
                <textarea
                  className="input-field min-h-20 resize-y"
                  value={editData.careerGoal}
                  onChange={(e) => updateField('careerGoal', e.target.value)}
                />
              ) : (
                <p className="text-sm text-slate-700 leading-relaxed">{profile.careerGoal}</p>
              )}
            </div>
          </div>

          {/* Job preferences: dùng cho tiêu chí "mong muốn" (15%) khi ghép nối */}
          <div className="card p-5">
            <div className="flex items-center gap-2 mb-1">
              <MapPin size={18} className="text-blue-600" />
              <h2 className="section-title text-sm">Mong muốn công việc</h2>
            </div>
            <p className="text-xs text-slate-400 mb-4">Chiếm 15% điểm phù hợp: khớp địa điểm và hình thức làm việc.</p>
            {[
              { label: 'Địa điểm', options: LOCATION_OPTIONS, selected: profile.preferredLocations, key: 'preferredLocations' as const },
              { label: 'Hình thức', options: WORK_TYPE_OPTIONS, selected: profile.preferredWorkTypes, key: 'preferredWorkTypes' as const },
            ].map((group) => (
              <div key={group.key} className="mb-3 last:mb-0">
                <div className="text-xs font-medium text-slate-500 mb-1.5">{group.label}</div>
                <div className="flex flex-wrap gap-1.5">
                  {group.options.map((opt) => {
                    const active = (group.selected as string[]).includes(opt);
                    if (!isEditing) {
                      return active ? <span key={opt} className="skill-tag">{opt}</span> : null;
                    }
                    return (
                      <button
                        key={opt}
                        onClick={() =>
                          group.key === 'preferredLocations'
                            ? updateField('preferredLocations', toggleItem(editData.preferredLocations, opt))
                            : updateField('preferredWorkTypes', toggleItem(editData.preferredWorkTypes, opt as WorkType))
                        }
                        className={`text-xs px-3 py-1.5 rounded-lg border transition-colors ${
                          active ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
                        }`}
                        aria-pressed={active}
                      >
                        {opt}
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>

          {/* Skills */}
          <div className="card p-5">
            <div className="flex items-center gap-2 mb-4">
              <Code2 size={18} className="text-blue-600" />
              <h2 className="section-title text-sm">Kỹ năng</h2>
            </div>
            <div className="flex flex-wrap gap-1.5 mb-3">
              {profile.skills.map((s) => (
                <span key={s} className="skill-tag flex items-center gap-1">
                  {s}
                  {isEditing && (
                    <button
                      onClick={() => removeSkill(s)}
                      className="text-blue-400 hover:text-red-500 transition-colors"
                      aria-label={`Xóa kỹ năng ${s}`}
                    >
                      <X size={11} />
                    </button>
                  )}
                </span>
              ))}
            </div>
            {isEditing && (
              <div className="flex gap-2">
                <input
                  className="input-field"
                  placeholder="Thêm kỹ năng mới..."
                  value={newSkill}
                  onChange={(e) => setNewSkill(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && addSkill()}
                />
                <button onClick={addSkill} className="btn-primary shrink-0">
                  <Plus size={16} />
                  Thêm
                </button>
              </div>
            )}
          </div>

          {/* Projects */}
          <div className="card p-5">
            <div className="flex items-center justify-between gap-2 mb-4">
              <div className="flex items-center gap-2">
                <Target size={18} className="text-blue-600" />
                <h2 className="section-title text-sm">Dự án cá nhân</h2>
              </div>
              {isEditing && (
                <button onClick={addProject} className="btn-secondary text-xs py-1.5">
                  <Plus size={14} />
                  Thêm dự án
                </button>
              )}
            </div>
            <div className="space-y-4">
              {isEditing
                ? editData.projects.map((proj, i) => (
                    <div key={proj.id} className="p-4 bg-slate-50 rounded-xl border border-slate-100 space-y-3">
                      <input
                        className="input-field"
                        placeholder="Tên dự án"
                        value={proj.name}
                        onChange={(e) => updateProject(i, { name: e.target.value })}
                      />
                      <textarea
                        className="input-field min-h-15 resize-y"
                        placeholder="Mô tả ngắn"
                        value={proj.description}
                        onChange={(e) => updateProject(i, { description: e.target.value })}
                      />
                      <input
                        key={`${proj.id}-tech`}
                        className="input-field"
                        placeholder="Công nghệ, cách nhau bằng dấu phẩy"
                        defaultValue={proj.technologies.join(', ')}
                        onBlur={(e) => updateProject(i, { technologies: parseList(e.target.value) })}
                      />
                      <div className="flex justify-end">
                        <button onClick={() => removeProject(i)} className="btn-danger text-xs py-1.5">
                          <Trash2 size={14} />
                          Xóa dự án
                        </button>
                      </div>
                    </div>
                  ))
                : profile.projects.map((proj) => (
                    <div key={proj.id} className="p-4 bg-slate-50 rounded-xl border border-slate-100">
                      <div className="font-semibold text-sm text-slate-800">{proj.name}</div>
                      <p className="text-xs text-slate-600 mt-1 leading-relaxed">{proj.description}</p>
                      <div className="flex flex-wrap gap-1 mt-2">
                        {proj.technologies.map((t) => (
                          <span key={t} className="badge-gray">{t}</span>
                        ))}
                      </div>
                      {proj.url && <div className="text-xs text-blue-500 mt-1.5 truncate">{proj.url}</div>}
                    </div>
                  ))}
              {profile.projects.length === 0 && !isEditing && (
                <p className="text-sm text-slate-400">Chưa có dự án nào.</p>
              )}
            </div>
          </div>

          {/* Experience */}
          <div className="card p-5">
            <div className="flex items-center justify-between gap-2 mb-4">
              <div className="flex items-center gap-2">
                <Briefcase size={18} className="text-blue-600" />
                <h2 className="section-title text-sm">Kinh nghiệm</h2>
              </div>
              {isEditing && (
                <button onClick={addExperience} className="btn-secondary text-xs py-1.5">
                  <Plus size={14} />
                  Thêm kinh nghiệm
                </button>
              )}
            </div>
            <div className="space-y-4">
              {isEditing
                ? editData.experience.map((exp, i) => (
                    <div key={exp.id} className="p-4 bg-slate-50 rounded-xl border border-slate-100 space-y-3">
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        <input
                          className="input-field"
                          placeholder="Vị trí"
                          value={exp.position}
                          onChange={(e) => updateExperience(i, { position: e.target.value })}
                        />
                        <input
                          className="input-field"
                          placeholder="Đơn vị / công ty"
                          value={exp.company}
                          onChange={(e) => updateExperience(i, { company: e.target.value })}
                        />
                      </div>
                      <input
                        className="input-field"
                        placeholder="Thời gian, ví dụ: Tháng 6/2025 – Tháng 9/2025"
                        value={exp.duration}
                        onChange={(e) => updateExperience(i, { duration: e.target.value })}
                      />
                      <textarea
                        className="input-field min-h-15 resize-y"
                        placeholder="Mô tả công việc"
                        value={exp.description}
                        onChange={(e) => updateExperience(i, { description: e.target.value })}
                      />
                      <div className="flex justify-end">
                        <button onClick={() => removeExperience(i)} className="btn-danger text-xs py-1.5">
                          <Trash2 size={14} />
                          Xóa
                        </button>
                      </div>
                    </div>
                  ))
                : profile.experience.map((exp) => (
                    <div key={exp.id} className="border-l-2 border-blue-200 pl-4">
                      <div className="font-semibold text-sm text-slate-800">{exp.position}</div>
                      <div className="text-xs text-blue-600 font-medium mt-0.5">{exp.company}</div>
                      <div className="text-xs text-slate-400 mt-0.5">{exp.duration}</div>
                      <p className="text-xs text-slate-600 mt-1.5 leading-relaxed">{exp.description}</p>
                    </div>
                  ))}
              {profile.experience.length === 0 && !isEditing && (
                <p className="text-sm text-slate-400">Chưa có kinh nghiệm nào.</p>
              )}
            </div>
          </div>
        </div>

        {/* Sidebar info */}
        <div className="space-y-5">
          {/* Avatar */}
          <div className="card p-5 text-center">
            <div className="w-20 h-20 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 font-bold text-2xl mx-auto mb-3">
              {studentProfile.fullName.split(' ').slice(-2).map((n) => n[0]).join('')}
            </div>
            <div className="font-bold text-slate-800">{studentProfile.fullName}</div>
            <div className="text-xs text-slate-400 mt-0.5">{studentProfile.major}</div>
            <div className="text-xs text-slate-400">{studentProfile.university}</div>

            {/* Liên kết hồ sơ: chỉ hiển thị, không lấy dữ liệu từ GitHub hay LinkedIn */}
            {isEditing ? (
              <div className="mt-3 space-y-2 text-left">
                <input
                  className="input-field text-xs"
                  placeholder="Link GitHub (https://github.com/...)"
                  value={editData.githubUrl ?? ''}
                  onChange={(e) => updateField('githubUrl', e.target.value)}
                />
                <input
                  className="input-field text-xs"
                  placeholder="Link LinkedIn (https://linkedin.com/in/...)"
                  value={editData.linkedinUrl ?? ''}
                  onChange={(e) => updateField('linkedinUrl', e.target.value)}
                />
              </div>
            ) : (
              (studentProfile.githubUrl || studentProfile.linkedinUrl) && (
                <div className="mt-3 space-y-1 text-left">
                  {[
                    ['GitHub', studentProfile.githubUrl],
                    ['LinkedIn', studentProfile.linkedinUrl],
                  ].map(([label, url]) =>
                    url ? (
                      <a
                        key={label}
                        href={url}
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-center gap-1.5 text-xs text-blue-600 hover:underline truncate"
                      >
                        <Link2 size={12} className="shrink-0" />
                        <span className="truncate">{label}: {url.replace(/^https?:\/\//, '')}</span>
                      </a>
                    ) : null
                  )}
                </div>
              )
            )}
          </div>

          {/* Nhập kỹ năng từ CV: đọc tệp trên trình duyệt, người dùng chọn kỹ năng cần thêm */}
          <CvImport profile={studentProfile} disabled={isEditing} onApply={updateProfile} />

          {/* Languages */}
          <div className="card p-5">
            <div className="flex items-center gap-2 mb-3">
              <GraduationCap size={16} className="text-blue-600" />
              <h2 className="section-title text-xs">Ngôn ngữ</h2>
            </div>
            <div className="space-y-1.5">
              {profile.languages.map((l, i) => (
                <div key={`${l}-${i}`} className="flex items-center gap-2 text-sm text-slate-700">
                  <div className="w-1.5 h-1.5 rounded-full bg-blue-400 shrink-0" />
                  <span className="flex-1 min-w-0 truncate">{l}</span>
                  {isEditing && (
                    <button
                      onClick={() => setEditData((prev) => ({ ...prev, languages: removeAt(prev.languages, i) }))}
                      className="text-slate-400 hover:text-red-500"
                      aria-label={`Xóa ngôn ngữ ${l}`}
                    >
                      <X size={12} />
                    </button>
                  )}
                </div>
              ))}
            </div>
            {isEditing && (
              <div className="flex gap-2 mt-3">
                <input
                  className="input-field"
                  placeholder="Ví dụ: Tiếng Nhật (N3)"
                  value={newLanguage}
                  onChange={(e) => setNewLanguage(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && addLanguage()}
                />
                <button onClick={addLanguage} className="btn-secondary shrink-0 px-3" aria-label="Thêm ngôn ngữ">
                  <Plus size={14} />
                </button>
              </div>
            )}
          </div>

          {/* Certificates */}
          <div className="card p-5">
            <div className="flex items-center justify-between gap-2 mb-3">
              <div className="flex items-center gap-2">
                <Award size={16} className="text-blue-600" />
                <h2 className="section-title text-xs">Chứng chỉ</h2>
              </div>
              {isEditing && (
                <button onClick={addCertificate} className="btn-secondary text-xs py-1 px-2" aria-label="Thêm chứng chỉ">
                  <Plus size={12} />
                </button>
              )}
            </div>
            <div className="space-y-3">
              {isEditing
                ? editData.certificates.map((cert, i) => (
                    <div key={cert.id} className="p-3 bg-slate-50 rounded-lg border border-slate-100 space-y-2">
                      <input
                        className="input-field"
                        placeholder="Tên chứng chỉ"
                        value={cert.name}
                        onChange={(e) => updateCertificate(i, { name: e.target.value })}
                      />
                      <div className="grid grid-cols-2 gap-2">
                        <input
                          className="input-field"
                          placeholder="Đơn vị cấp"
                          value={cert.issuer}
                          onChange={(e) => updateCertificate(i, { issuer: e.target.value })}
                        />
                        <input
                          className="input-field"
                          placeholder="Năm"
                          value={cert.year}
                          onChange={(e) => updateCertificate(i, { year: e.target.value })}
                        />
                      </div>
                      <div className="flex justify-end">
                        <button onClick={() => removeCertificate(i)} className="text-xs text-red-500 hover:underline">
                          Xóa chứng chỉ
                        </button>
                      </div>
                    </div>
                  ))
                : profile.certificates.map((cert) => (
                    <div key={cert.id}>
                      <div className="font-medium text-xs text-slate-800">{cert.name}</div>
                      <div className="text-xs text-slate-400">{cert.issuer} · {cert.year}</div>
                    </div>
                  ))}
              {profile.certificates.length === 0 && !isEditing && (
                <p className="text-xs text-slate-400">Chưa có chứng chỉ nào.</p>
              )}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
